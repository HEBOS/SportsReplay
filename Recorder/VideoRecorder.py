#!/usr/bin/env python3
import threading
import time
import math
import cv2
from multiprocessing import connection
import numpy as np
import socket
import errno
import sys
import psutil
import queue
from Shared.SharedFunctions import SharedFunctions
from Shared.CvFunctions import CvFunctions
from Shared.Camera import Camera
from Shared.CapturedFrame import CapturedFrame, SharedCapturedFrameHandler
from Shared.RecordScreenInfo import RecordScreenInfo
from Shared.RecordScreenInfoEventItem import RecordScreenInfoEventItem
from Shared.RecordScreenInfoOperation import RecordScreenInfoOperation


class VideoRecorder(object):
    def __init__(self, camera: Camera,
                 ai_frame_connection: connection.Connection, video_frame_connection: connection.Connection,
                 screen_connection: connection.Connection,  detection_connection: connection.Connection,
                 debugging: bool):
        self.camera = camera
        self.ai_frame_connection = ai_frame_connection
        self.video_frame_connection = video_frame_connection
        self.detection_frequency = math.floor(camera.fps / camera.cdfps)
        self.screen_connection = screen_connection
        self.detection_connection = detection_connection
        self.debugging = debugging

        #p = psutil.Process()
        #p.cpu_affinity([1 + camera.id])

        self.capturing = False
        self.capture_lock = threading.Lock()

        # We assume that the active camera is 1
        self.active_camera_id = 1
        self.active_detection = None

        self.ai_frames_queue = queue.Queue(maxsize=100)
        self.video_frames_queue = queue.Queue(maxsize=100)
        self.frame_dispatching = True
        self.frame_dispatching_lock = threading.Lock()
        self.frame_dispatcher_thread = threading.Thread(target=self.dispatch_frames,
                                                        args=(self.ai_frames_queue,
                                                              self.ai_frame_connection,
                                                              "ai"))
        self.video_dispatcher_thread = threading.Thread(target=self.dispatch_frames,
                                                        args=(self.video_frames_queue,
                                                              self.video_frame_connection,
                                                              "video"))

    def start(self):
        self.frame_dispatcher_thread.start()
        self.video_dispatcher_thread.start()
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
            print("Video camera {}".format(self.camera.id))
            print(self.camera.source)
            print("")
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
                    cv2.waitKey(1)

                    if total_frames % 10 == 0:
                        print("FRAMES GRABBED: {}".format(total_frames))

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

                        self.ai_frames_queue.put_nowait(captured_frame)

                    # Check if the camera activity has changed
                    try:
                        if self.detection_connection.poll():
                            self.active_detection = self.detection_connection.recv()
                            self.active_camera_id = self.active_detection.camera_id
                    except EOFError:
                        pass
                    except socket.error as e:
                        if e.errno != errno.EPIPE:
                            # Not a broken pipe
                            raise e
                    finally:
                        pass

                    # Pass it to VideoMaker process, but only for active camera
                    if self.active_camera_id == self.camera.id:
                        try:
                            self.video_frames_queue.put_nowait(CapturedFrame(self.camera,
                                                                             frame_number,
                                                                             snapshot_time,
                                                                             frame,
                                                                             SharedFunctions.get_recording_time(
                                                                                 self.camera.start_of_capture,
                                                                                 capture.get(cv2.CAP_PROP_POS_MSEC))))
                        except Exception as e:
                            print(SharedFunctions.get_exception_info(e))
                            raise e

                    self.screen_connection.send([RecordScreenInfoEventItem(RecordScreenInfo.VR_HEART_BEAT,
                                                                           RecordScreenInfoOperation.SET,
                                                                           self.camera.id),
                                                 RecordScreenInfoEventItem(RecordScreenInfo.VR_QUEUE_COUNT,
                                                                           RecordScreenInfoOperation.SET,
                                                                           self.video_frames_queue.qsize())
                                                 ])

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
                raise e
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

        self.frame_dispatching = False
        self.frame_dispatcher_thread.join()
        self.video_dispatcher_thread.join()

        try:
            if capture is not None:
                capture.release()
            CvFunctions.release_open_cv()
            SharedCapturedFrameHandler.send_frame(self.ai_frame_connection, None, "ai")
            SharedCapturedFrameHandler.send_frame(self.video_frame_connection, None, "video")
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

    def dispatch_frames(self, q: queue.Queue, conn: connection.Connection, name_prefix: str):
        frame_dispatching = True
        while frame_dispatching:
            with self.frame_dispatching_lock:
                frame_dispatching = self.frame_dispatching
            if q.qsize() > 0:
                captured_frame: CapturedFrame = q.get()
                SharedCapturedFrameHandler.send_frame(conn, captured_frame, name_prefix)


