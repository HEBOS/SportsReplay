#!/usr/bin/env python3
import jetson.inference
import jetson.utils
import os
import time
import cv2
from typing import List
from Shared.LogHandler import LogHandler
from Shared.CapturedFrame import CapturedFrame
from Shared.Detection import Detection
from Shared.MultiProcessingQueue import MultiProcessingQueue


class Detector(object):
    def __init__(self, playground: int, ai_queues: List[MultiProcessingQueue], class_id: int, network: str,
                 threshold: float, video_queue: MultiProcessingQueue):
        self.playground = playground
        self.ai_queues = ai_queues
        self.class_id = class_id
        self.network = network
        self.threshold = threshold
        self.video_queue = video_queue
        self.detecting = False
        # Logger
        self.logger = LogHandler("detector")


    def detect(self):
        self.detecting = True

        # load the object detection network
        net = jetson.inference.detectNet(self.network,
                                         [],
                                         float(self.threshold))
        try:
            active_camera = 1
            while self.detecting:
                # Determine queue of active camera
                active_camera_queue: MultiProcessingQueue = self.ai_queues[active_camera - 1]

                # We only proceed, if there is anything in active camera queu
                if not active_camera_queue.is_empty():
                    active_camera_frame: CapturedFrame = \
                        active_camera_queue.dequeue("Ai Queue {}".format(active_camera))

                    # We are stopping detection if we have reached the end of the queue
                    # Also, we need to remove all queues to reclaim the used memory
                    if active_camera_frame is None:
                        for index, ai_queue in enumerate(self.ai_queues):
                            while not ai_queue.is_empty():
                                captured_frame: CapturedFrame = ai_queue.dequeue("AI Queue {}".format(index + 1))
                                if captured_frame is not None:
                                    captured_frame.release()
                                    del captured_frame

                        print("Detector - break after active camera frame is None.")
                        self.detecting = False
                        break

                    # If we have found the candidate that needs AI detection, we put it in the detection list
                    if active_camera_frame.detect_candidate:
                        candidate_frames = [active_camera_frame]

                        # Also, we are dequeuing frames from all other queues, so that we find the same point in time,
                        # so that the comparison between real situation on the field can take place
                        for index, ai_queue in enumerate(self.ai_queues):
                            if index != active_camera - 1:
                                while True:
                                    if not ai_queue.is_empty():
                                        other_camera_frame: CapturedFrame = \
                                            ai_queue.dequeue("AI Queue {}".format(index + 1))
                                        if other_camera_frame is not None:
                                            if other_camera_frame.timestamp >= active_camera_frame.timestamp:
                                                candidate_frames.append(other_camera_frame)
                                                break
                                        else:
                                            print("Detector - poison pill detected - exiting...")
                                            self.detecting = False
                                            break

                        # Now that we have all frames that represent exact time when that situation took place,
                        # we run the detection
                        for captured_frame in candidate_frames:
                            if captured_frame is not None:

                                start_time = time.time()
                                rgba = cv2.cvtColor(captured_frame.frame, cv2.COLOR_RGB2RGBA)
                                image = jetson.utils.cudaFromNumpy(rgba)

                                # Before detection starts, we push frames from active camera to video queue, and
                                # discard frames from other cameras, to resolve the problem with detection letancy
                                timestamp_stopper = active_camera_frame.get_future_timestamp(
                                    int((1 / active_camera_frame.camera.cdfps * active_camera_frame.camera.fps) * 1.6))
                                self.video_queue.enqueue(active_camera_frame, "Video Queue")
                                self.forward_frames(timestamp_stopper, int(active_camera))

                                # Run the AI detection, based on class id
                                detections = net.Detect(image, 1280, 720)
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
                                                               detection.Instance))

                                del detections

                                # Save largest ball size information on captured frame
                                captured_frame.largest_ball_size = self.get_largest_ball_size(balls)
                                print("Detection took = {}".format(time.time() - start_time))

                        # Determine the active camera
                        active_camera, active_camera_capture_frame = self.determine_active_camera(candidate_frames,
                                                                                                  active_camera)
                        print("Active camera = {}".format(active_camera))
                    else:
                        self.video_queue.enqueue(active_camera_frame, "Video Queue")
                        # We are removing frames from all other cameras too
                        for index, ai_queue in enumerate(self.ai_queues):
                            if index != active_camera - 1:
                                while True:
                                    if not ai_queue.is_empty():
                                        other_camera_frame: CapturedFrame = \
                                            ai_queue.dequeue("AI Queue {}".format(index + 1))
                                        if other_camera_frame is not None:
                                            if other_camera_frame.timestamp >= active_camera_frame.timestamp:
                                                break
                                        else:
                                            print("Detector - poison pill detected - exiting...")
                                            self.detecting = False
                                            break

            print("Detector - normal exit.")
        except Exception as ex:
            print("ERROR: {}".format(ex))
        finally:
            self.video_queue.mark_as_done()
            print("Detector finished working.")

    def get_largest_ball_size(self, balls: List[Detection]) -> int:
        max_size = 0
        if len(balls) > 1:
            print("There are {} balls detected.".format(len(balls)))

        for ball in balls:
            max_size = max(max_size, ball.get_ball_size())

        return max_size

    def determine_active_camera(self, captured_frames: List[CapturedFrame], active_camera) -> (int, CapturedFrame):
        largest_ball_size_in_all_frames = 0

        # Get largest ball in across all frames
        for capture_frame in captured_frames:
            largest_ball_size_in_all_frames = max(largest_ball_size_in_all_frames, capture_frame.largest_ball_size)

        # Now determine the active camera
        for capture_frame in captured_frames:
            if capture_frame.largest_ball_size == largest_ball_size_in_all_frames:
                # Note if the active camera contains the ball of that size, we preserve the activity of that camera
                if capture_frame.camera.id == active_camera:
                    return active_camera, capture_frame
                else:
                    # Otherwise, we select first camera, which contains the largest ball as an active one
                    return capture_frame.camera.id, capture_frame

    def forward_frames(self, timestamp_stopper: float, active_camera: int) -> bool:
        print("Fast forwarding to {}".format(timestamp_stopper))
        for index, ai_queue in enumerate(self.ai_queues):
            if index != active_camera - 1:
                while self.detecting:
                    if not ai_queue.is_empty():
                        other_camera_frame: CapturedFrame = \
                            ai_queue.dequeue("AI Queue {}".format(index + 1))
                        if other_camera_frame is not None:
                            if other_camera_frame.timestamp < timestamp_stopper:
                                del other_camera_frame
                            else:
                                break
                        else:
                            print("Detector - poison pill detected - exiting...")
                            return False
            else:
                while self.detecting:
                    if not ai_queue.is_empty():
                        active_camera_frame: CapturedFrame = \
                            ai_queue.dequeue("AI Queue {}".format(index + 1))
                        if active_camera_frame is not None:
                            if active_camera_frame.timestamp < timestamp_stopper:
                                self.video_queue.enqueue(active_camera_frame, "Video Queue")
                                del active_camera_frame
                            else:
                                break
                        else:
                            print("Detector - poison pill detected - exiting...")
                            return False

        return True
