#!/usr/bin/env python3
from threading import Lock
import time
import math
import cv2
import numpy as np
import multiprocessing as mp
from Shared.SharedFunctions import SharedFunctions
from Shared.CvFunctions import CvFunctions
from Shared.Camera import Camera
from Shared.CapturedFrame import CapturedFrame, SharedCapturedFrameHandler as sch
from Shared.RecordScreenInfo import RecordScreenInfo
from Shared.RecordScreenInfoEventItem import RecordScreenInfoEventItem
from Shared.RecordScreenInfoOperation import RecordScreenInfoOperation


class VideoRecorder(object):
    VIDEO: str = "video"
    AI: str = "ai"

    def __init__(self, camera: Camera, ai_frame_queue: mp.Queue, video_frame_queue: mp.Queue, screen_queue: mp.Queue,
                 detection_queue: mp.Queue, debugging: bool):
        self.camera = camera
        self.ai_frame_queue = ai_frame_queue
        self.video_frame_queue = video_frame_queue
        self.screen_queue = screen_queue
        self.detection_queue = detection_queue
        self.detection_frequency = math.floor(camera.fps / camera.cdfps)
        self.debugging = debugging

        # We assume that the active camera is 1
        self.active_camera_id = 1
        self.active_detection = None

    def start(self):
        # Sync the start with other cameras, so they start at the same time
        while self.camera.start_of_capture > time.time():
            time.sleep(.010)

        try:
            self.screen_queue.put_nowait([RecordScreenInfoEventItem(RecordScreenInfo.VR_RECORDING_START_SCHEDULED,
                                                                    RecordScreenInfoOperation.SET,
                                                                    time.strftime("%Y-%m-%d-%H-%M-%S",
                                                                                  time.gmtime(
                                                                                     self.camera.start_of_capture))),
                                          RecordScreenInfoEventItem(RecordScreenInfo.VR_RECORDING_STARTED,
                                                                    RecordScreenInfoOperation.SET,
                                                                    time.strftime("%Y-%m-%d-%H-%M-%S",
                                                                                  time.gmtime(time.time()))),
                                          RecordScreenInfoEventItem(RecordScreenInfo.VR_RECORDING_END_SCHEDULED,
                                                                    RecordScreenInfoOperation.SET,
                                                                    time.strftime("%Y-%m-%d-%H-%M-%S",
                                                                                  time.gmtime(
                                                                                      self.camera.end_of_capture)))
                                          ])
        except Exception as e:
            pass

        capture = None
        total_frames = 0

        try:
            # Initialise the capture
            print("Video camera {}".format(self.camera.id))
            print(self.camera.source)
            print("")
            capture = cv2.VideoCapture(self.camera.source, cv2.CAP_GSTREAMER)
            snapshot_time = time.time()
            frame_number = 0

            grabbed = False
            # Do until it is expected
            while time.time() < self.camera.end_of_capture:
                # Grab the next frame. Used for more precise results.
                grabbed = capture.grab()
                if grabbed:
                    total_frames += 1
                    frame_number += 1
                    if (frame_number > self.camera.fps + 1) or (int(time.time()) > int(snapshot_time)):
                        frame_number = 1

                    snapshot_time = time.time()

                    # Determine if the frame is a detection candidate.
                    detection_candidate = frame_number % self.detection_frequency == 1

                    # Get the frame itself
                    ref, frame = capture.retrieve()

                    # Check if the camera activity has changed
                    self.check_active_detection()

                    # Detection candidate should be handled by Detector, that will send an active camera change
                    # message, short time after, so that a correct image in video_queue can be written to the stream
                    # Note that we are passing the copy of the image, to avoid it being freed by video maker process
                    if detection_candidate and self.active_camera_id != self.camera.id:
                        captured_frame = CapturedFrame(self.camera,
                                                       frame_number,
                                                       snapshot_time,
                                                       np.copy(frame),
                                                       SharedFunctions.get_recording_time(
                                                           self.camera.start_of_capture,
                                                           capture.get(cv2.CAP_PROP_POS_MSEC)))

                        self.ai_frame_queue.put_nowait(sch.get_shared_frame(captured_frame,
                                                                            self.AI))

                    dddf = cv2.CAP_PROP_POS_MSEC
                    self.video_frame_queue.put_nowait(
                        sch.get_shared_frame(CapturedFrame(self.camera,
                                                           frame_number,
                                                           snapshot_time,
                                                           frame,
                                                           SharedFunctions.get_recording_time(
                                                               self.camera.start_of_capture,
                                                               capture.get(
                                                                   cv2.CAP_PROP_POS_MSEC))), self.VIDEO))

                if total_frames % (self.camera.fps * 2) == 0:
                    self.screen_queue.put_nowait([RecordScreenInfoEventItem(RecordScreenInfo.VR_HEART_BEAT,
                                                                            RecordScreenInfoOperation.SET,
                                                                            self.camera.id),
                                                  RecordScreenInfoEventItem(RecordScreenInfo.VR_QUEUE_COUNT,
                                                                            RecordScreenInfoOperation.SET,
                                                                            self.video_frame_queue.qsize()),
                                                 RecordScreenInfoEventItem(RecordScreenInfo.AI_QUEUE_COUNT,
                                                                           RecordScreenInfoOperation.SET,
                                                                           self.ai_frame_queue.qsize())
                                                  ])

            self.screen_queue.put_nowait([RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                                                    RecordScreenInfoOperation.SET,
                                                                    "Camera {}, on playground {} finished recording.".
                                                                    format(self.camera.id, self.camera.playground))])
            self.screen_queue.put_nowait([RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                                                    RecordScreenInfoOperation.SET,
                                                                    "Expected ending {}. Ending at {}".
                                                                    format(time.gmtime(self.camera.end_of_capture),
                                                                           time.gmtime(time.time())))])
        except cv2.error as e:
            self.screen_queue.put_nowait([RecordScreenInfoEventItem(RecordScreenInfo.VR_EXCEPTIONS,
                                                                    RecordScreenInfoOperation.ADD,
                                                                    1),
                                          RecordScreenInfoEventItem(RecordScreenInfo.ERROR_LOG,
                                                                    RecordScreenInfoOperation.SET,
                                                                    "Camera {}, on playground {} is not responding.".
                                                                    format(self.camera.id, self.camera.playground))])
        except Exception as ex:
            self.screen_queue.put_nowait([RecordScreenInfoEventItem(RecordScreenInfo.VR_EXCEPTIONS,
                                                                    RecordScreenInfoOperation.ADD,
                                                                    1),
                                          RecordScreenInfoEventItem(RecordScreenInfo.ERROR_LOG,
                                                                    RecordScreenInfoOperation.SET,
                                                                    SharedFunctions.get_exception_info(ex))])

        try:
            if capture is not None:
                capture.release()
            CvFunctions.release_open_cv()
            self.ai_frame_queue.put_nowait(None)
            self.video_frame_queue.put_nowait(None)
            print("TOTAL FRAMES GRABBED: {}".format(total_frames))
        except Exception as ex:
            pass

    def cv2error(self):
        self.screen_queue.put_nowait([RecordScreenInfoEventItem(RecordScreenInfo.VR_EXCEPTIONS,
                                                                RecordScreenInfoOperation.ADD,
                                                                1),
                                      RecordScreenInfoEventItem(RecordScreenInfo.ERROR_LOG,
                                                                RecordScreenInfoOperation.SET,
                                                                "Camera {}, on playground {} is not responding."
                                                                .format(self.camera.id, self.camera.playground))
                                      ])

    def check_active_detection(self):
        # Check if there is a message from Detector that active camera has changed
        try:
            if self.detection_queue.qsize() > 0:
                self.active_detection = self.detection_queue.get()
                self.active_camera_id = self.active_detection.camera_id
        except Exception as ex:
            raise ex
        finally:
            pass
