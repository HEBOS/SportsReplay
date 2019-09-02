#!/usr/bin/env python3
import jetson.inference
import jetson.utils
import cv2
import multiprocessing as mp
import time
import jsonpickle
from typing import List
from Shared.LogHandler import LogHandler
from Shared.CapturedFrame import CapturedFrame
from Shared.Camera import Camera
from Shared.Detection import Detection
from Shared.MultiProcessingQueue import MultiProcessingQueue
from Shared.Linq import Linq
from Shared.SharedFunctions import SharedFunctions
from Shared.DefinedPolygon import DefinedPolygon


class Detector(object):
    def __init__(self, playground: int, ai_queue: MultiProcessingQueue, video_queue: MultiProcessingQueue,
                 class_id: int, network: str, threshold: float, width: int, height: int,
                 cameras: List[Camera], detection_connection: mp.connection.Connection,
                 polygons: List[DefinedPolygon], debugging: bool):
        self.playground = playground
        self.ai_queue = ai_queue
        self.video_queue = video_queue
        self.class_id = class_id
        self.network = network
        self.threshold = threshold
        self.width = width
        self.height = height
        self.cameras = cameras
        self.detection_connection = detection_connection
        self.polygons = polygons
        self.debugging = debugging
        self.detecting = False
        self.active_camera = cameras[0]

        # Logger
        self.logger = LogHandler("detector")

    def start(self):
        self.detecting = True

        # load the object detection network
        net = jetson.inference.detectNet(self.network,
                                         [],
                                         float(self.threshold))
        try:
            ballsizes: List[Detection] = []
            while self.detecting:
                # We only proceed, if there is anything in the active camera queue
                if not self.ai_queue.is_empty():
                    captured_frame: CapturedFrame = self.ai_queue.dequeue("Ai Queue {}".format(self.active_camera.id))

                    # We are stopping detection if we have reached the end of the queue
                    if captured_frame is None:
                        break

                    start_time = time.time()

                    # This increases the fps of AI detection
                    size = (480, 272)

                    rgba = cv2.cvtColor(cv2.resize(captured_frame.frame, size), cv2.COLOR_RGB2RGBA)
                    image = jetson.utils.cudaFromNumpy(rgba)

                    # Run the AI detection, based on class id
                    detections = net.Detect(image, size[0], size[1])
                    jetson.utils.cudaDeviceSynchronize()
                    del image

                    # Convert detections into balls
                    balls = []
                    for detection in detections:
                        if detection.ClassID == self.class_id:
                            balls.append(Detection(detection.Left,
                                                   detection.Right,
                                                   detection.Top,
                                                   detection.Bottom,
                                                   detection.Width,
                                                   detection.Height,
                                                   detection.Confidence,
                                                   detection.Instance,
                                                   captured_frame.camera.id,
                                                   int(captured_frame.snapshot_time) +
                                                   captured_frame.frame_number / 10000))

                    # Some logging for debug session
                    if self.debugging:
                        print("Detection took = {}".format(time.time() - start_time))
                        if len(balls) > 0:
                            print("Detection details {}".format(jsonpickle.encode(balls)))
                        self.logger.info("Time {}. Camera {}. Detection result - {} balls."
                                         .format(captured_frame.timestamp,
                                                 captured_frame.camera.id,
                                                 len(balls)))
                        if len(balls) == 1 and self.debugging:
                            ballsizes.append(balls[0])

                    del detections

                    if len(balls) > 0:
                        # We declare the examining camera as an active one if there is a ball in the area it covers
                        # but the ball is not in protected area
                        for ball in balls:
                            if ball.confidence > 0.11:
                                if Linq(self.polygons).any(
                                        lambda p: p.camera_id == ball.camera_id and
                                                  p.detect and p.contains_ball(ball)) and \
                                        not Linq(self.polygons).any(
                                            lambda p: p.camera_id == ball.camera_id and
                                                      (not p.detect) and p.contains_ball(ball)):

                                    if self.active_camera.id != ball.camera_id:
                                        # Change active camera
                                        self.active_camera = self.cameras[ball.camera_id - 1]
                                        # Send message, which will be received by Recorder,
                                        # and dispatched to all VideoRecorder instances
                                        self.detection_connection.send(ball)
                                        self.logger.info("Camera {} became active.".format(self.active_camera.id))
                                    break

                            # Preserve information about last detection, no matter, if we changed the camera or not
                            camera = self.cameras[captured_frame.camera.id - 1]
                            camera.last_detection = time.time()

            if self.debugging:
                self.log_balls(ballsizes)
            print("Detector - normal exit.")
        except Exception as ex:
            print("ERROR: {}".format(ex))
        finally:
            self.detection_connection.close()
            self.video_queue.mark_as_done()
            print("Detector finished working.")

    def log_balls(self, ball_sizes: List[Detection]):
        ballsizes_lines: List[str] = ["height\twidth\tleft\tright\ttop\tbottom\tconfidence"
                                      "\tcamera\tframe_number\r\n"]
        for bs in ball_sizes:
            ballsizes_lines.append(
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
        SharedFunctions.create_list_file(r"/home/sportsreplay/tmp/recording/detected-balls.txt", ballsizes_lines)
