#!/usr/bin/env python3
import cv2
from multiprocessing import connection
import time
import numpy as np
import threading
import os
import socket
import errno
import copy
import psutil
from typing import List
from Shared.CapturedFrame import CapturedFrame, SharedCapturedFrameHandler
from Shared.Camera import Camera
from Shared.Detection import Detection
from Shared.Linq import Linq
from Shared.SharedFunctions import SharedFunctions
from Shared.DefinedPolygon import DefinedPolygon
from Darknet.DarknetDetector import DarknetDetector
from Shared.RecordScreenInfo import RecordScreenInfo
from Shared.RecordScreenInfoEventItem import RecordScreenInfoEventItem
from Shared.RecordScreenInfoOperation import RecordScreenInfoOperation


class Detector(object):
    def __init__(self, playground: int, ai_frame_connections: List[connection.Connection],
                 class_id: int, network_config_path: str, network_weights_path: str,
                 coco_config_path: str, width: int, height: int,
                 cameras: List[Camera], detection_connections: List[connection.Connection],
                 polygons: List[DefinedPolygon], screen_connection: connection.Connection,
                 debugging: bool, number_of_cameras: int):
        #p = psutil.Process()
        #p.cpu_affinity([0])
        self.playground = playground
        self.ai_frame_connections = ai_frame_connections
        self.class_id = class_id
        self.network_config_path = network_config_path
        self.network_weights_path = network_weights_path
        self.coco_config_path = coco_config_path
        self.width = width
        self.height = height
        self.cameras = cameras
        self.detection_connections = detection_connections
        self.polygons = polygons
        self.debugging = debugging
        self.active_camera = cameras[0]
        self.screen_connection = screen_connection
        self.number_of_cameras_to_process = number_of_cameras

        # Logger
        self.total_detections = 0
        self.detection_started = time.time()

    def start(self):
        # load the object detection network
        net: DarknetDetector = DarknetDetector(self.network_config_path,
                                               self.network_weights_path,
                                               self.coco_config_path,
                                               (self.cameras[0].width, self.cameras[0].height))

        self.detection_started = time.time()

        try:
            ball_sizes: List[Detection] = []

            warmed_up = False
            last_job = time.time()
            last_camera_swapping = time.time() - 2
            detecting = True
            while detecting:
                # We only proceed, if there is anything in the active camera queue
                for conn in self.ai_frame_connections:
                    has_frame, captured_frame = SharedCapturedFrameHandler.get_frame(conn)
                    if has_frame:
                        last_job = time.time()
                        warmed_up = True

                        # We are stopping detection if we have reached the end of the queue for all cameras
                        if captured_frame is None:
                            self.number_of_cameras_to_process -= 1
                            if self.number_of_cameras_to_process <= 0:
                                detecting = False
                                break
                        elif (captured_frame is not None) and captured_frame.camera.id == self.active_camera.id:
                            captured_frame.release()
                        elif (captured_frame is not None) and captured_frame.camera.id != self.active_camera.id:
                            # Run the AI detection, based on class id
                            detections = net.detect(captured_frame.frame, True)

                            # Convert detections into balls
                            balls = []
                            for detection in detections:
                                if detection.ClassID == self.class_id:
                                    balls.append(Detection(int(detection.Left),
                                                           int(detection.Right),
                                                           int(detection.Top),
                                                           int(detection.Bottom),
                                                           int(detection.Width),
                                                           int(detection.Height),
                                                           detection.Confidence,
                                                           captured_frame.camera.id,
                                                           int(captured_frame.snapshot_time) +
                                                           captured_frame.frame_number / 10000))

                            # Some logging for debug session
                            if self.debugging:
                                if len(balls) == 1 and self.debugging:
                                    ball_sizes.append(balls[0])
                            else:
                                if len(balls) > 0:
                                    self.total_detections += 1

                            if len(balls) > 0:
                                self.total_detections += 1
                                detections_per_second = (self.total_detections / (time.time() - self.detection_started))
                                self.screen_connection.send(
                                    [RecordScreenInfoEventItem(RecordScreenInfo.AI_DETECTIONS_PER_SECOND,
                                                               RecordScreenInfoOperation.SET,
                                                               detections_per_second)])

                                # We declare the examining camera as an active one,
                                # if there is a ball in the area it covers, but the ball is not in protected area
                                for ball in balls:
                                    if Linq(self.polygons).any(
                                            lambda p: p.camera_id == ball.camera_id and
                                            p.detect and p.contains_ball(ball)) and \
                                            not Linq(self.polygons).any(
                                                lambda p: p.camera_id == ball.camera_id and
                                                (not p.detect) and p.contains_ball(ball)):

                                        if self.active_camera.id != ball.camera_id:
                                            # Change active camera, but only after 1 second
                                            if time.time() - last_camera_swapping > 1:
                                                self.active_camera = self.cameras[ball.camera_id - 1]
                                                last_camera_swapping = time.time()

                                                # Send message to VideoMaker process
                                                for detect_connection in self.detection_connections:
                                                    detect_connection.send(copy.copy(ball))

                                                self.screen_connection.send(
                                                    [RecordScreenInfoEventItem(RecordScreenInfo.VR_ACTIVE_CAMERA,
                                                                               RecordScreenInfoOperation.SET,
                                                                               ball.camera_id),
                                                     RecordScreenInfoEventItem(RecordScreenInfo.AI_IS_LIVE,
                                                                               RecordScreenInfoOperation.SET,
                                                                               "yes")]
                                                )
                                                if self.debugging:
                                                    debug_thread = \
                                                        threading.Thread(target=self.draw_debug_info,
                                                                         args=(copy.deepcopy(captured_frame), ball))
                                                    debug_thread.start()
                                        break

                                    # Preserve information about last detection, no matter,
                                    # if we changed the camera or not
                                    camera = self.cameras[captured_frame.camera.id - 1]
                                    camera.last_detection = time.time()
                            captured_frame.release()
                    else:
                        # This ensures, that this process exits, if it has processed at least one frame,
                        # and hasn't got any other during the next 5 seconds.
                        if warmed_up:
                            if time.time() - last_job > 10:
                                self.screen_connection.send(
                                    [RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                                               RecordScreenInfoOperation.SET,
                                                               "Detector - Exit due to no activity.")])
                                detecting = False
                                break

            if self.debugging:
                Detector.log_balls(ball_sizes)

            self.screen_connection.send([RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                                                   RecordScreenInfoOperation.SET,
                                                                   "Detector finished working.")])
        except EOFError:
            pass
        except socket.error as e:
            if e.errno != errno.EPIPE:
                # Not a broken pipe
                raise e
        except Exception as ex:
            self.screen_connection.send(
                [RecordScreenInfoEventItem(RecordScreenInfo.AI_EXCEPTIONS,
                                           RecordScreenInfoOperation.ADD,
                                           1),
                 RecordScreenInfoEventItem(RecordScreenInfo.AI_IS_LIVE,
                                           RecordScreenInfoOperation.SET,
                                           "no"),
                 RecordScreenInfoEventItem(RecordScreenInfo.ERROR_LOG,
                                           RecordScreenInfoOperation.SET,
                                           SharedFunctions.get_exception_info(ex))]
            )
        finally:
            try:
                SharedFunctions.close_connection(self.screen_connection)
                for conn in self.detection_connections:
                    SharedFunctions.close_connection(conn)
                for conn in self.ai_frame_connections:
                    SharedFunctions.close_connection(conn)
            except EOFError:
                pass
            except socket.error as e:
                pass
            except Exception as ex:
                print(ex)

    @staticmethod
    def log_balls(ball_sizes: List[Detection]):
        ball_sizes_lines: List[str] = ["height\twidth\tleft\tright\ttop\tbottom\tconfidence\tcamera\tframe_number\r\n"]
        for bs in ball_sizes:
            ball_sizes_lines.append(
                "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\r\n".format(bs.height,
                                                                bs.width,
                                                                bs.left,
                                                                bs.right,
                                                                bs.top,
                                                                bs.bottom,
                                                                bs.confidence,
                                                                bs.camera_id,
                                                                bs.frame_number)

            )
        SharedFunctions.create_list_file(r"/home/sportsreplay/tmp/recording/detected-balls.txt", ball_sizes_lines)

    def draw_debug_info(self, captured_frame: CapturedFrame, ball: Detection):
        # Draw protected area first
        for polygon_definition in self.polygons:
            if polygon_definition.camera_id == captured_frame.camera.id:
                points = SharedFunctions.get_points_array(polygon_definition.points, self.width / 480)
                pts = np.array(points, np.int32)
                pts = pts.reshape((-1, 1, 2))
                border_color = (255, 0, 0) if not polygon_definition.detect else (0, 0, 0)
                cv2.polylines(captured_frame.frame, [pts], True, border_color)

        # Draw last detection
        points = SharedFunctions.get_points_array(ball.points, self.width / 480)
        pts = np.array(points, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(captured_frame.frame, [pts], True, (52, 158, 190))

        cv2.putText(captured_frame.frame, "Confidence={}%".format(ball.confidence * 100),
                    (10, 500), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

        dump_file_path = os.path.join(captured_frame.camera.session_path,
                                      "frame-{}-{}-{}.jpg".format(int(captured_frame.snapshot_time),
                                                                  str(captured_frame.frame_number).zfill(4),
                                                                  captured_frame.camera.id))
        cv2.imwrite(dump_file_path, captured_frame.frame)
