#!/usr/bin/env python3
import threading
import time
import math
import cv2
import multiprocessing as mp
import numpy as np
import socket
import errno
import os
import sys
from Shared.SharedFunctions import SharedFunctions
from Shared.CvFunctions import CvFunctions
from Shared.Camera import Camera
from Shared.CapturedFrame import CapturedFrame
from Shared.MultiProcessingQueue import MultiProcessingQueue
from Shared.RecordScreenInfo import RecordScreenInfo
from Shared.RecordScreenInfoEventItem import RecordScreenInfoEventItem
from Shared.RecordScreenInfoOperation import RecordScreenInfoOperation


class VideoRecorder(object):
    def __init__(self, camera: Camera, ai_queue: MultiProcessingQueue, video_queue: MultiProcessingQueue,
                 screen_connection: mp.connection.Connection, debugging: bool):
        self.init_stdout = sys.stdout
        self.camera = camera
        self.ai_queue = ai_queue
        self.video_queue = video_queue
        self.debugging = debugging
        self.detection_frequency = math.floor(camera.fps / camera.cdfps)
        self.screen_connection = screen_connection

        self.capturing = False
        self.capture_lock = threading.Lock()
        
    def start(self):
        self.capturing = True

        # Sync the start with other cameras, so they start at the same time
        while self.camera.start_of_capture > time.time():
            time.sleep(.010)

        try:
            self.screen_connection.send([RecordScreenInfoEventItem(RecordScreenInfo.VR_RECORDING_START_SCHEDULED,
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
        except EOFError:
            pass
        except socket.error as e:
            pass

        capture = None
        total_frames = 0

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
                    total_frames += 1
                    frame_number += 1
                    if (frame_number > self.camera.fps + 1) or (int(time.time()) > int(snapshot_time)):
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
                                                       np.copy(frame),
                                                       SharedFunctions.get_recording_time(
                                                           self.camera.start_of_capture,
                                                           capture.get(cv2.CAP_PROP_POS_MSEC)))

                        self.ai_queue.enqueue(captured_frame, "AI Queue {}".format(self.camera.id))
                        self.screen_connection.send([RecordScreenInfoEventItem(RecordScreenInfo.AI_QUEUE_COUNT,
                                                                               RecordScreenInfoOperation.SET,
                                                                               self.ai_queue.qsize())])

                    # Pass it to VideoMaker process
                    self.video_queue.enqueue(CapturedFrame(self.camera,
                                                           frame_number,
                                                           snapshot_time,
                                                           frame,
                                                           SharedFunctions.get_recording_time(
                                                               self.camera.start_of_capture,
                                                               capture.get(cv2.CAP_PROP_POS_MSEC))),
                                             "Video Queue")
                    self.screen_connection.send([RecordScreenInfoEventItem(RecordScreenInfo.VR_HEART_BEAT,
                                                                           RecordScreenInfoOperation.SET,
                                                                           self.camera.id)])

            self.screen_connection.send([RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                                                   RecordScreenInfoOperation.SET,
                                                                   "Camera {}, on playground {} finished recording.".
                                                                   format(self.camera.id, self.camera.playground))])

            self.screen_connection.send([RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                                                   RecordScreenInfoOperation.SET,
                                                                   "Expected ending {}. Ending at {}".
                                                                   format(time.gmtime(self.camera.end_of_capture),
                                                                          time.gmtime(time.time())))])
        except EOFError:
            pass
        except socket.error as e:
            if e.errno != errno.EPIPE:
                # Not a broken pipe
                raise
        except cv2.error as e:
            self.capturing = False
            self.screen_connection.send([RecordScreenInfoEventItem(RecordScreenInfo.VR_EXCEPTIONS,
                                                                   RecordScreenInfoOperation.ADD,
                                                                   1),
                                         RecordScreenInfoEventItem(RecordScreenInfo.ERROR_LOG,
                                                                   RecordScreenInfoOperation.SET,
                                                                   "Camera {}, on playground {} is not responding.".
                                                                   format(self.camera.id, self.camera.playground))])
        except Exception as ex:
            self.capturing = False
            self.screen_connection.send([RecordScreenInfoEventItem(RecordScreenInfo.VR_EXCEPTIONS,
                                                                   RecordScreenInfoOperation.ADD,
                                                                   1),
                                         RecordScreenInfoEventItem(RecordScreenInfo.ERROR_LOG,
                                                                   RecordScreenInfoOperation.SET,
                                                                   SharedFunctions.get_exception_info(ex))])
        try:
            self.screen_connection.close()
            self.screen_connection = None
            if capture is not None:
                capture.release()
            CvFunctions.release_open_cv()
            self.ai_queue.mark_as_done()
            self.video_queue.mark_as_done()
            self.ai_queue = None
            self.video_queue = None
            print("TOTAL FRAMES GRABBED: {}".format(total_frames))
        except EOFError:
            pass
        except socket.error as e:
            pass
        except Exception as ex:
            print(ex)

    def cv2error(self):
        self.screen_connection.send([RecordScreenInfoEventItem(RecordScreenInfo.VR_EXCEPTIONS,
                                                               RecordScreenInfoOperation.ADD,
                                                               1),
                                     RecordScreenInfoEventItem(RecordScreenInfo.ERROR_LOG,
                                                               RecordScreenInfoOperation.SET,
                                                               "Camera {}, on playground {} is not responding."
                                                               .format(self.camera.id, self.camera.playground))
                                     ])

