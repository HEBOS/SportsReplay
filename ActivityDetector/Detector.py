#!/usr/bin/env python3
import cv2
import time
import numpy as np
import os
import copy
import multiprocessing as mp
import threading
from typing import List
from Shared.CapturedFrame import CapturedFrame, SharedCapturedFrameHandler as sch
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
    def __init__(self, playground: int,
                 ai_frame_queue: mp.Queue, detection_queues: List[mp.Queue], screen_queue: mp.Queue,
                 class_id: int, network_config_path: str, network_weights_path: str,
                 coco_config_path: str, width: int, height: int,
                 cameras: List[Camera], polygons: List[DefinedPolygon], number_of_cameras: int,
                 debugging: bool):
        self.playground = playground
        self.ai_frame_queue = ai_frame_queue
        self.detection_queues = detection_queues
        self.screen_queue = screen_queue

        self.class_id = class_id
        self.network_config_path = network_config_path
        self.network_weights_path = network_weights_path
        self.coco_config_path = coco_config_path
        self.width = width
        self.height = height
        self.cameras = cameras
        self.polygons = polygons
        self.number_of_cameras_to_process = number_of_cameras
        self.debugging = debugging

        self.active_camera = cameras[0]

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
            while True:
                # We only proceed, if there is anything in the active camera queue
                if self.ai_frame_queue.qsize() > 0:
                    shared_captured_frame = self.ai_frame_queue.get()
                    last_job = time.time()
                    warmed_up = True

                    # We are stopping detection if we have reached the end of the queue for all cameras
                    if shared_captured_frame is not None:
                        captured_frame = sch.get_frame(shared_captured_frame)
                        # Run the AI detection, based on class id
                        print("Detecting frame from camera {}".format(captured_frame.camera.id))
                        detections = net.detect(captured_frame.frame, True)
                        self.total_detections += 1
                        detections_per_second = (self.total_detections / (time.time() - self.detection_started))
                        self.screen_queue.put_nowait(
                            [RecordScreenInfoEventItem(RecordScreenInfo.AI_DETECTIONS_PER_SECOND,
                                                       RecordScreenInfoOperation.SET,
                                                       detections_per_second)])

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
                                                       captured_frame.frame_number / 10000,
                                                       captured_frame.timestamp))

                        # Some logging for debug session
                        if self.debugging:
                            if len(balls) == 1 and self.debugging:
                                ball_sizes.append(balls[0])
                        else:
                            if len(balls) > 0:
                                self.total_detections += 1

                        if len(balls) > 0:
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
                                            for detection_queue in self.detection_queues:
                                                detection_queue.put_nowait(copy.copy(ball))

                                            self.screen_queue.put_nowait(
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
                        break
                else:
                    # This ensures, that this process exits, if it has processed at least one frame,
                    # and hasn't got any other during the next 5 seconds.
                    if warmed_up:
                        if time.time() - last_job > 10:
                            self.screen_queue.put_nowait(
                                [RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                                           RecordScreenInfoOperation.SET,
                                                           "Detector - Exit due to no activity.")])
                            break

            if self.debugging:
                Detector.log_balls(ball_sizes)

            self.screen_queue.put_nowait([RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                                                    RecordScreenInfoOperation.SET,
                                                                    "Detector finished working.")])

        except Exception as ex:
            self.screen_queue.put_nowait(
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
