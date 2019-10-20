#!/usr/bin/env python3
import cv2
import time
import numpy as np
import multiprocessing as mp
from typing import List
import os
import sys
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


class VideoMaker(object):
    def __init__(self, playground: int, video_queue: MultiProcessingQueue, output_video: str,
                 latency: float, detection_connection: mp.connection.Connection,
                 polygons: List[DefinedPolygon], width: int, height: int, fps: int,
                 screen_connection: mp.connection.Connection, debugging: bool):
        self.playground = playground
        self.video_queue = video_queue
        self.output_video = output_video
        self.latency = latency
        self.detection_connection = detection_connection
        self.polygons = polygons
        self.width = width
        self.height = height
        self.debugging = debugging
        self.fps = fps
        self.video_creating = False
        self.screen_connection = screen_connection

        # We assume that the active camera is 1
        self.active_camera_id = 1
        self.active_detection = None

    def start(self):
        self.video_creating = True
        output_pipeline = "appsrc " \
                          "! videoconvert " \
                          "! video/x-raw,width={width},height={height},format=I420,framerate={fps}/1 " \
                          "! omxh264enc " \
                          "! h264parse " \
                          "! qtmux " \
                          "! filesink location={video}".format(width=self.width,
                                                               height=self.height,
                                                               fps=self.fps,
                                                               video=self.output_video)

        try:
            writer = cv2.VideoWriter(output_pipeline,
                                     cv2.VideoWriter_fourcc(*'mp4v'),
                                     self.fps,
                                     (self.width, self.height),
                                     True)

            i = 0
            warmed_up = False
            last_job = time.time()
            while True:
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

                    # Delay rendering so that Detector can notify VideoMaker a bit earlier, before camera has switched
                    if captured_frame is not None and time.time() >= captured_frame.timestamp - self.latency:
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

                        if captured_frame is None:
                            break
                        else:
                            if captured_frame.camera.id == self.active_camera_id:
                                if self.active_detection is not None and self.debugging:
                                    self.draw_debug_info(captured_frame)

                                writer.write(captured_frame.frame)

                                if i % self.fps == 0:
                                    self.screen_connection.send(
                                        [RecordScreenInfoEventItem(RecordScreenInfo.VM_WRITTEN_FRAMES,
                                                                   RecordScreenInfoOperation.SET,
                                                                   i)])
                else:
                    # This ensures, that this process exits, if it has processed at least one frame,
                    # and hasn't got any other during the next 5 seconds.
                    if warmed_up:
                        if time.time() - last_job > 5:
                            break

            writer.release()
            self.screen_connection.send(
                [RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                           RecordScreenInfoOperation.SET,
                                           "VideoMaker ended.")])
        except EOFError:
            pass
        except socket.error as e:
            if e.errno != errno.EPIPE:
                # Not a broken pipe
                raise
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
                points = SharedFunctions.get_points_array(polygon_definition.points, 1280 / 480)
                pts = np.array(points, np.int32)
                pts = pts.reshape((-1, 1, 2))
                border_color = (255, 0, 0) if not polygon_definition.detect else (0, 0, 0)
                cv2.polylines(captured_frame.frame, [pts], True, border_color)

        # Draw last detection
        if self.active_detection.camera_id == self.active_camera_id:
            points = SharedFunctions.get_points_array(self.active_detection.points, 1280 / 480)
            pts = np.array(points, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(captured_frame.frame, [pts], True, (52, 158, 190))

        frame_info = int(captured_frame.snapshot_time) + captured_frame.frame_number / 10000
        cv2.putText(captured_frame.frame, str(frame_info),
                    (10, 500), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)
