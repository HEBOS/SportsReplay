#!/usr/bin/env python3
import cv2
import time
import numpy as np
import multiprocessing as mp
from typing import List
import os
import gc
import socket
import errno
from Shared.CapturedFrame import CapturedFrame
from Shared.SharedFunctions import SharedFunctions
from Shared.CvFunctions import CvFunctions
from Shared.MultiProcessingQueue import MultiProcessingQueue
from Shared.DefinedPolygon import DefinedPolygon
from Shared.RecordScreenInfo import RecordScreenInfo
from Shared.RecordScreenInfoEventItem import RecordScreenInfoEventItem
from Shared.RecordScreenInfoOperation import RecordScreenInfoOperation
from Shared.Configuration import Configuration
from Shared.LogoRenderer import LogoRenderer


class VideoMaker(object):
    def __init__(self, playground: int, video_queue: MultiProcessingQueue, output_video: str,
                 video_latency: float, detection_connection: mp.connection.Connection,
                 polygons: List[DefinedPolygon], width: int, height: int, fps: int,
                 screen_connection: mp.connection.Connection, debugging: bool):
        self.config = Configuration()
        self.playground = playground
        self.video_queue = video_queue
        self.output_video = output_video
        self.video_latency = video_latency
        self.detection_connection = detection_connection
        self.polygons = polygons
        self.width = width
        self.height = height
        self.debugging = debugging
        self.fps = fps
        self.screen_connection = screen_connection

        # We assume that the active camera is 1
        self.active_camera_id = 1
        self.active_detection = None

        self.time_format = self.config.common["time-format"]
        self.date_format = self.config.common["date-format"]
        self.resized_overlay_image: np.ndarray = LogoRenderer.get_resized_overlay(
            os.path.join(os.getcwd(), self.config.video_maker["logo-path"]), self.width)

        self.writer = None

    def start(self):
        output_pipeline = "appsrc " \
                          "! capsfilter caps='video/x-raw,format=I420,framerate={fps}/1' " \
                          "! videoconvert " \
                          "! capsfilter caps='video/x-raw,format=BGRx,interpolation-method=1' " \
                          "! nvvideoconvert " \
                          "! capsfilter caps='video/x-raw(memory:NVMM)' " \
                          "! nvv4l2h264enc maxperf-enable=true " \
                          "! h264parse " \
                          "! qtmux " \
                          "! filesink location={video}".format(width=self.width,
                                                               height=self.height,
                                                               fps=self.fps,
                                                               video=self.output_video)

        if self.debugging:
            print("gst-launch-1.0 {}".format(output_pipeline))

        self.writer = cv2.VideoWriter(output_pipeline,
                                      cv2.VideoWriter_fourcc(*'mp4v'),
                                      self.fps,
                                      (self.width, self.height),
                                      True)
        try:
            i = 0
            written_frames = 0
            warmed_up = False
            last_job = time.time()
            while True:
                try:
                    if not self.video_queue.is_empty():
                        last_job = time.time()
                        warmed_up = True
                        i += 1

                        captured_frame: CapturedFrame = self.video_queue.dequeue("Video Queue")
                        self.screen_connection.send([RecordScreenInfoEventItem(RecordScreenInfo.VM_QUEUE_COUNT,
                                                                               RecordScreenInfoOperation.SET,
                                                                               self.video_queue.qsize()),
                                                     RecordScreenInfoEventItem(RecordScreenInfo.VM_IS_LIVE,
                                                                               RecordScreenInfoOperation.SET,
                                                                               "yes")
                                                     ])

                        # Delay rendering so that Detector can notify VideoMaker a bit earlier,
                        # before camera has switched
                        if captured_frame is not None:
                            if time.time() >= captured_frame.timestamp - self.video_latency:
                                # Check if there is a message from Detector that active camera change has happen
                                try:
                                    if self.detection_connection.poll():
                                        self.active_detection = self.detection_connection.recv()
                                        self.active_camera_id = self.active_detection.camera_id
                                except EOFError:
                                    pass
                                except socket.error as e:
                                    if e.errno != errno.EPIPE:
                                        # Not a broken pipe
                                        raise
                                finally:
                                    pass

                                if captured_frame.camera.id == self.active_camera_id:
                                    if (self.active_detection is not None) and self.debugging:
                                        self.draw_debug_info(captured_frame)
                                    LogoRenderer.draw_logo(captured_frame.frame,
                                                           self.resized_overlay_image,
                                                           self.date_format,
                                                           self.time_format,
                                                           captured_frame.camera_time)

                                    self.writer.write(captured_frame.frame)
                                    written_frames += 1
                                    captured_frame.release()
                                    if captured_frame.frame_number % self.fps == 0:
                                        gc.collect()

                                    self.screen_connection.send(
                                        [RecordScreenInfoEventItem(RecordScreenInfo.VM_WRITTEN_FRAMES,
                                                                   RecordScreenInfoOperation.SET,
                                                                   written_frames)])
                                else:
                                    captured_frame.release()
                                    if i % self.fps == 0:
                                        gc.collect()
                            else:
                                captured_frame.release()
                                if i % self.fps == 0:
                                    gc.collect()
                    else:
                        # This ensures, that this process exits, if it has processed at least one frame,
                        # and hasn't got any other during the next 5 seconds.
                        if warmed_up:
                            if time.time() - last_job > 5:
                                break
                except EOFError:
                    pass
                except socket.error as e:
                    if e.errno != errno.EPIPE:
                        # Not a broken pipe
                        raise

            self.writer.release()
            self.screen_connection.send(
                [RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                           RecordScreenInfoOperation.SET,
                                           "VideoMaker ended.")])
        except Exception as ex:
            self.screen_connection.send(
                [RecordScreenInfoEventItem(RecordScreenInfo.VM_EXCEPTIONS,
                                           RecordScreenInfoOperation.ADD,
                                           1),
                 RecordScreenInfoEventItem(RecordScreenInfo.VM_IS_LIVE,
                                           RecordScreenInfoOperation.SET,
                                           "no"),
                 RecordScreenInfoEventItem(RecordScreenInfo.ERROR_LOG,
                                           RecordScreenInfoOperation.SET,
                                           SharedFunctions.get_exception_info(ex))]
            )
        finally:
            try:
                self.detection_connection.close()
                self.detection_connection = None
                self.screen_connection.close()
                self.screen_connection = None
                CvFunctions.release_open_cv()
            except EOFError:
                pass
            except socket.error as e:
                pass
            except Exception as ex:
                print(ex)

    def draw_debug_info(self, captured_frame: CapturedFrame):
        # Draw protected area first
        for polygon_definition in self.polygons:
            if polygon_definition.camera_id == captured_frame.camera.id:
                points = SharedFunctions.get_points_array(polygon_definition.points, self.width / 480)
                pts = np.array(points, np.int32)
                pts = pts.reshape((-1, 1, 2))
                border_color = (255, 0, 0) if not polygon_definition.detect else (0, 0, 0)
                cv2.polylines(captured_frame.frame, [pts], True, border_color)

        # Draw last detection
        if self.active_detection.camera_id == self.active_camera_id:
            points = SharedFunctions.get_points_array(self.active_detection.points, self.width / 480)
            pts = np.array(points, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(captured_frame.frame, [pts], True, (52, 158, 190))

        frame_info = int(captured_frame.snapshot_time) + captured_frame.frame_number / 10000
        cv2.putText(captured_frame.frame, str(frame_info),
                    (10, 500), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

