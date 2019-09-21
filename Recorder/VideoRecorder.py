import threading
import time
import logging
import math
import cv2
import numpy as np
from Shared.LogHandler import LogHandler
from Shared.SharedFunctions import SharedFunctions
from Shared.Camera import Camera
from Shared.CapturedFrame import CapturedFrame
from Shared.MultiProcessingQueue import MultiProcessingQueue


class VideoRecorder(object):
    def __init__(self, camera: Camera, ai_queue: MultiProcessingQueue, video_queue: MultiProcessingQueue,
                 debugging: bool):
        self.camera = camera
        self.ai_queue = ai_queue
        self.video_queue = video_queue
        self.debugging = debugging
        self.detection_frequency = math.floor(camera.fps / camera.cdfps)

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

        capture = None
        try:
            # Initialise the capture
            capture = cv2.VideoCapture(self.camera.source, cv2.CAP_GSTREAMER)
            snapshot_time = time.time()
            frame_number = 0

            # Do until it is expected
            while (time.time() < self.camera.end_of_capture) and self.capturing:
                # Grab the next frame. Used for more precise results.
                grabbed = capture.grab()
                if grabbed:
                    frame_number += 1
                    if frame_number > self.camera.fps + 1 or int(time.time()) > int(snapshot_time):
                        frame_number = 1

                    snapshot_time = time.time()

                    # Determine if the frame is a detection candidate.
                    detection_candidate = frame_number % self.detection_frequency == 1

                    # Get the frame itself
                    ref, frame = capture.retrieve()

                    # Detection candidate should be handled by Detector, that will send an active camera change
                    # message, short time after, so that a correct image in video_queue can be written to the stream
                    # Note that we are passing the copy of the image, to avoid it being freed by video maker process
                    if detection_candidate:
                        captured_frame = CapturedFrame(self.camera,
                                                       frame_number,
                                                       snapshot_time,
                                                       np.copy(frame))
                        self.ai_queue.enqueue(captured_frame, "AI Queue {}".format(self.camera.id))

                    # Pass it to VideoMaker process
                    self.video_queue.enqueue(CapturedFrame(self.camera,
                                                           frame_number,
                                                           snapshot_time,
                                                           frame), "Video Queue")

        except cv2.error as e:
            self.capturing = False
            self.logger.error("Camera {}, on playground {} is not responding."
                              .format(self.camera.id, self.camera.playground))
        finally:
            if capture is not None:
                capture.release()
            SharedFunctions.release_open_cv()
            self.ai_queue.mark_as_done()
            self.video_queue.mark_as_done()
            self.ai_queue = None
            self.video_queue = None
            print("Camera {}, on playground {} finished recording."
                  .format(self.camera.id, self.camera.playground))
            print("Expected ending {}. Ending at {}".format(self.camera.end_of_capture, time.time()))

    def cv2error(self):
        self.logger.error("Camera {}, on playground {} is not responding."
                          .format(self.camera.id, self.camera.playground))

