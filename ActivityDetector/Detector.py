#!/usr/bin/env python3
import threading
import jetson.inference
import jetson.utils
import os
import multiprocessing as mp
import queue as queue
from typing import List
from Shared.LogHandler import LogHandler
from Shared.CapturedFrame import CapturedFrame
from Shared.Detection import Detection


class Detector(object):
    def __init__(self, playground: int, ai_queues: List[mp.Queue], class_id: int, network: str, threshold: float,
                 width: int, height: int, fps: int, output_video: str):
        self.playground = playground
        self.ai_queues = ai_queues
        self.class_id = class_id
        self.network = network
        self.threshold = threshold
        self.video_creating = True
        self.video_creator_queue = queue.Queue()
        self.video_creator_thread = threading.Thread(target=self.create_video, args=())
        self.width = width
        self.height = height
        self.fps = fps
        self.output_video = output_video

        # Logger
        self.logger = LogHandler("detector")

    def detect(self):
        detecting = True
        self.video_creator_thread.start()

        # load the object detection network
        net = jetson.inference.detectNet(self.network,
                                         [],
                                         float(self.threshold))

        active_camera = 1

        try:
            while detecting:
                # Determine queue of active camera
                active_camera_queue: mp.Queue = self.ai_queues[active_camera - 1]

                # We only proceed, if there is anything in active camera queu
                if not active_camera_queue.empty():
                    active_camera_frame: CapturedFrame = active_camera_queue.get()

                    # We are stopping detection if we have reached the end of the queue
                    # Also, we need to remove all queues to reclaim the used memory
                    if active_camera_frame is None:
                        for index, ai_queue in enumerate(self.ai_queues):
                            while not ai_queue.empty():
                                ai_queue.get()
                        break

                    # If we have found the candidate that needs AI detection, we put it in the detection list
                    if active_camera_frame.detect_candidate:
                        detection_frames = [active_camera_frame]

                        # Also, we are dequeuing frames from all other queues, so that we find the same point in time,
                        # so that the comparison between real situation on the field can take place
                        for index, ai_queue in enumerate(self.ai_queues):
                            if index != active_camera:
                                while True:
                                    other_camera_frame: CapturedFrame = ai_queue.get()
                                    if other_camera_frame.timestamp >= active_camera_frame:
                                        detection_frames.append(other_camera_frame)
                                        break

                        # Now that we have all frames that represent exact time that situation took place,
                        # we run the detection
                        for index, captured_frame in detection_frames:
                            if captured_frame is not None:

                                # If the file really exists on the disk, we load the file into memory, and
                                # remove it from the disk afterwards
                                if os.path.isfile(captured_frame.filePath):
                                    image, width, height = jetson.utils.loadImageRGBA(captured_frame.filePath)
                                    captured_frame.remove_file()

                                    # Run the AI detection, based on class id
                                    detections = net.Detect(image, width, height)

                                    # Wait for cuda to process results
                                    if len(detections) > 0:
                                        jetson.utils.cudaDeviceSynchronize()

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

                                    # Save largest ball size information on captured frame
                                    captured_frame.largest_ball_size = self.get_largest_ball_size(balls)

                        # Determine the active camera
                        active_camera, active_camera_capture_frame = self.determine_active_camera(detection_frames,
                                                                                                  active_camera)
                        # Pass the active camera frame to Video Creator
                        self.video_creator_queue.put(active_camera_capture_frame)
        finally:
            self.video_creating = False
            self.video_creator_thread.join()

    def create_video(self):
        out = cv2.VideoWriter(self.output_video, cv2.VideoWriter_fourcc(*'DIVX'), self.fps, (self.width, self.height))

        while self.video_creating or not self.video_creator_queue.empty():
            capture_frame: CapturedFrame = self.video_creator_queue.get()
            out.write(capture_frame.frame)

        out.release()

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
                    # Otherwise, we select the first of the cameras that contain the largest ball as an active one
                    return capture_frame.camera.id, capture_frame

