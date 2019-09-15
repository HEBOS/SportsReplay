import threading
import time
import multiprocessing as mp
import logging
import math
import cv2
import gc
import numpy as np
from typing import List
from Shared.LogHandler import LogHandler
from Shared.SharedFunctions import SharedFunctions
from Shared.Camera import Camera
from Shared.CapturedFrame import CapturedFrame
from Shared.MultiProcessingQueue import MultiProcessingQueue
from Shared.DefinedPolygon import DefinedPolygon


class VideoRecorder(object):
    def __init__(self, camera: Camera, ai_queue: MultiProcessingQueue, video_queue: MultiProcessingQueue,
                 detection_connection: mp.connection.Connection, polygons: List[DefinedPolygon], debugging: bool):
        self.camera = camera
        self.ai_queue = ai_queue
        self.video_queue = video_queue
        self.polygons = polygons
        self.debugging = debugging
        self.detection_connection = detection_connection
        self.detection_frequency = math.floor(camera.fps / camera.cdfps)

        # We asume that the active camera is 1
        self.active_camera_id = 1
        self.active_detection = None

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
                        self.active_detection = self.detection_connection.recv()
                        self.active_camera_id = self.active_detection.camera_id
                finally:
                    pass

                # Determine if the frame is a detection candidate.
                detection_candidate = frame_number % self.detection_frequency == 1

                if grabbed:
                    if detection_candidate or self.active_camera_id == self.camera.id:
                        ref, frame = capture.retrieve()

                        # Detection candidate should be handled by Detector, that will send an active camera change
                        # message, short time after, so that a correct instance of VideoRecorder can take over
                        # the camera activity. Note that we are passing the copy of the image, to avoid it being
                        # freed by video maker process
                        if detection_candidate:
                            captured_frame = CapturedFrame(self.camera,
                                                           frame_number,
                                                           snapshot_time,
                                                           np.copy(frame))
                            self.ai_queue.enqueue(captured_frame, "AI Queue {}".format(self.camera.id))

                        # If this is the recorder for the active camera, we push the frame into video stream
                        if self.active_camera_id == self.camera.id:
                            if self.active_detection is not None and self.debugging:
                                frame = self.draw_debug_info(frame, int(snapshot_time) + frame_number / 10000)

                            # Ensure this is recorder by VideoMaker process
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
            self.detection_connection.close()
            self.ai_queue.mark_as_done()
            self.video_queue.mark_as_done()
            self.ai_queue = None
            self.video_queue = None
            print("Camera {}, on playground {} finished recording."
                  .format(self.camera.id, self.camera.playground))
            print("Expected ending {}. Ending at {}".format(self.camera.end_of_capture, time.time()))

    def draw_debug_info(self, img: np.array, frame_info: float):
        # Draw protected area first
        for polygon_definition in self.polygons:
            if polygon_definition.camera_id == self.camera.id:
                points = SharedFunctions.get_points_array(polygon_definition.points, 1280 / 480)
                pts = np.array(points, np.int32)
                pts = pts.reshape((-1, 1, 2))
                border_color = (255, 0, 0) if not polygon_definition.detect else (0, 0, 0)
                cv2.polylines(img, [pts], True, border_color)

        # Draw last detection
        if self.active_detection.camera_id == self.active_camera_id:
            points = SharedFunctions.get_points_array(self.active_detection.points, 1280 / 480)
            pts = np.array(points, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(img, [pts], True, (52, 158, 190))

        cv2.putText(img, str(frame_info),
                    (10, 500), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)
        return img

    def cv2error(self):
        self.logger.error("Camera {}, on playground {} is not responding."
                          .format(self.camera.id, self.camera.playground))

