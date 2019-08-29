import threading
import time
import multiprocessing as mp
import logging
import os
import math
import cv2
from Shared.LogHandler import LogHandler
from Shared.SharedFunctions import SharedFunctions
from Shared.Camera import Camera
from Shared.CapturedFrame import CapturedFrame
from Shared.MultiProcessingQueue import MultiProcessingQueue


class VideoRecorder(object):
    def __init__(self, camera: Camera, ai_queue: MultiProcessingQueue, video_queue: MultiProcessingQueue,
                 detection_connection: mp.connection.Connection):
        #os.sched_setaffinity(0, {2, 3})
        self.camera = camera
        self.ai_queue = ai_queue
        self.video_queue = video_queue
        self.detection_connection = detection_connection
        self.detection_frequency = math.floor(camera.fps / camera.cdfps)

        # We asume that the active camera is 1
        self.active_camera_id = 1

        # Logger
        self.logger = LogHandler("recording-camera-{}".format(camera.id))
        self.logger.info('Camera {}, on playground {} has started recording.'.format(camera.id, camera.playground))

        self.capturing = False
        self.capture_lock = threading.Lock()
        
    def start(self):
        self.capturing = True

        # Sync the start with other cameras, so they start at the same time
        while self.camera.start_of_capture > time.time():
            time.sleep(.010)
        print("Expected start {}. Started at {}".format(self.camera.start_of_capture, time.time()))

        try:
            capture = cv2.VideoCapture(self.camera.source, cv2.CAP_GSTREAMER)
            #capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera.width)
            #capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera.height)
            #capture.set(cv2.CAP_PROP_FPS, self.camera.fps)
            #capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            #capture.set(cv2.CAP_PROP_EXPOSURE, -8)
            snapshot_time = time.time()
            frame_number = 0

            while (time.time() < self.camera.end_of_capture) and self.capturing:
                with self.capture_lock:
                    if not self.capturing:
                        break

                # Wait for the next time trigger
                while time.time() - snapshot_time <= 1 / self.camera.fps:
                    pass

                frame_number += 1
                if frame_number > self.camera.fps + 1 or int(time.time()) > int(snapshot_time):
                    frame_number = 1

                snapshot_time = time.time()

                # Grab the next frame. Used for more precise results.
                grabbed = capture.grab()

                # Check if there is a message from Detector that active camera change has happen
                try:
                    if self.detection_connection.poll():
                        new_active_camera_id = self.detection_connection.recv()
                        self.active_camera_id = new_active_camera_id
                finally:
                    pass

                # Determine if the frame is a detection candidate.
                detection_candidate = frame_number % self.detection_frequency == 1

                if grabbed:
                    if detection_candidate or self.active_camera_id == self.camera.id:
                        ref, frame = capture.retrieve(flag=0)

                        # If this is the recorder for the active camera, we push the frame into video stream
                        if self.active_camera_id == self.camera.id:
                            self.video_queue.enqueue(CapturedFrame(self.camera,
                                                                   frame_number,
                                                                   snapshot_time,
                                                                   frame), "Video Queue")

                        # Detection candidate should be handled by Detector, that will send an active camera change
                        # message, short time after, so that a correct instance of VideoRecorder can take over
                        # the camera activity
                        if detection_candidate:
                            captured_frame = CapturedFrame(self.camera,
                                                           frame_number,
                                                           snapshot_time,
                                                           frame)
                            self.ai_queue.enqueue(captured_frame, "AI Queue {}".format(self.camera.id))

        except cv2.error as e:
            self.capturing = False
            self.logger.error("Camera {}, on playground {} is not responding."
                              .format(self.camera.id, self.camera.playground))
        finally:
            self.ai_queue.mark_as_done()
            self.video_queue.mark_as_done()
            self.detection_connection.close()

            print("Camera {}, on playground {} finished recording."
                  .format(self.camera.id, self.camera.playground))
            SharedFunctions.release_open_cv()
            print("Expected ending {}. Ending at {}".format(self.camera.end_of_capture, time.time()))

    def cv2error(self):
        self.logger.error("Camera {}, on playground {} is not responding."
                          .format(self.camera.id, self.camera.playground))

