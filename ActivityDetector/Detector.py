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
from Shared.IgnoredPolygon import IgnoredPolygon


class Detector(object):
    def __init__(self, playground: int, ai_queue: MultiProcessingQueue, video_queue: MultiProcessingQueue,
                 class_id: int, network: str, threshold: float, width: int, height: int,
                 cameras: List[Camera], detection_connection: mp.connection.Connection,
                 ignored_polygons: List[IgnoredPolygon]):
        #os.sched_setaffinity(0, {0})
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
        self.ignored_polygons = ignored_polygons
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
                                                   int(captured_frame.snapshot_time) + captured_frame.frame_number / 10000))

                    # Save largest ball size information on captured frame
                    detected_largest_ball_size, detection = self.get_largest_ball_size(balls)
                    print("Detection took = {}".format(time.time() - start_time))

                    if len(balls) > 0:
                        print("Detection details {}".format(jsonpickle.encode(balls)))

                    self.logger.info("Time {}. Camera {}. Detection result - {} balls."
                                     .format(captured_frame.timestamp,
                                             captured_frame.camera.id,
                                             len(balls)))

                    del detections

                    if len(balls) == 1:
                        ballsizes.append(balls[0])

                    if len(balls) == 1 and balls[0].confidence >= 0.13:
                        # We declare the above camera as an active one if all other cameras have smaller ball,
                        # but we check
                        # the last time we were checking
                        if Linq(self.cameras).all(lambda c: c != captured_frame.camera.id and
                                                  c.largest_ball_size < detected_largest_ball_size):
                            self.active_camera = self.cameras[captured_frame.camera.id - 1]
                            # Send message, which will be received by Recorder,
                            # and dispatched to all VideoRecorder instances
                            self.detection_connection.send(detection)
                            self.logger.info("Camera {} became active.".format(self.active_camera.id))
                            # As we have changed the activity of the camera, we need to set
                            # the size of the ball on all other cameras to zero
                            for other_camera in self.cameras:
                                if other_camera.id != self.active_camera.id:
                                    other_camera.largest_ball_size = 0

                        # We need to save the results of detection in our camera
                        camera = self.cameras[captured_frame.camera.id - 1]
                        camera.largest_ball_size = detected_largest_ball_size
                        camera.last_detection = time.time()

            self.log_ballsizes(ballsizes)
            print("Detector - normal exit.")
        except Exception as ex:
            print("ERROR: {}".format(ex))
        finally:
            self.video_queue.mark_as_done()
            self.detection_connection.close()
            print("Detector finished working.")

    def get_largest_ball_size(self, balls: List[Detection]) -> (int, Detection):
        max_size = 0
        detection = None
        if len(balls) > 1:
            print("There are {} balls detected.".format(len(balls)))

        for ball in balls:
            ignore_ball = False
            for polygon in self.ignored_polygons:
                if polygon.camera_id == ball.camera_id and polygon.contains_ball(ball):
                    ignore_ball = True
                    break

            if not ignore_ball:
                max_size = max(max_size, ball.ball_size)
                if max_size == ball.ball_size:
                    detection = ball
            else:
                print("BALL INSIDE IGNORED POLYGONNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN")

        return max_size, detection

    def log_ballsizes(self, ball_sizes: List[Detection]):
        ballsizes_lines: List[str] = ["height\twidth\tleft\tright\ttop\tbottom\tball size\tconfidence"
                                      "\tcamera\tframe_number\r\n"]
        for bs in ball_sizes:
            ballsizes_lines.append(
                "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\r\n".format(bs.height,
                                                                    bs.width,
                                                                    bs.left,
                                                                    bs.right,
                                                                    bs.top,
                                                                    bs.bottom,
                                                                    bs.ball_size,
                                                                    bs.confidence,
                                                                    bs.camera_id,
                                                                    bs.frame_number)

            )
        SharedFunctions.create_list_file(r"/home/sportsreplay/tmp/recording/ballsizes.txt", ballsizes_lines)
