import threading
import time
import logging
import math
import cv2
from Shared.LogHandler import LogHandler
from Shared.SharedFunctions import SharedFunctions
from Shared.Camera import Camera
from Shared.CapturedFrame import CapturedFrame
from Shared.MultiProcessingQueue import MultiProcessingQueue


class VideoRecorder(object):
    def __init__(self, camera: Camera, ai_queue: MultiProcessingQueue):
        self.camera = camera
        self.ai_queue = ai_queue

        # Logger
        self.logger = LogHandler("recording")
        self.logger.info('Camera {}, on playground {} has started recording.'.format(camera.id, camera.playground))

        # Capturing support
        self.capture_lock = threading.Lock()
        self.capture = None
        self.capturing = False
        self.capture_thread = None

        self.detection_frequency = math.floor(camera.fps / camera.cdfps)

    def start(self):
        try:
            with self.capture_lock:
                self.capturing = True
            self.capture_thread = threading.Thread(target=self.record, args=())
            self.capture_thread.start()

            while (time.time() < self.camera.end_of_capture) and self.capturing:
                time.sleep(1)
        except Exception as ex:
            print(ex)
            self.logger.error("Camera {}, on playground {} is not responding."
                              .format(self.camera.id, self.camera.playground))

        finally:
            with self.capture_lock:
                self.capturing = False
            self.capture_thread.join()

            SharedFunctions.release_open_cv()
            print("Expected ending {}. Ending at {}".format(self.camera.end_of_capture, time.time()))

    def record(self):
        # Sync the start with other cameras, so they start at the same time
        while self.camera.start_of_capture > time.time():
            time.sleep(.010)
        print("Expected start {}. Started at {}".format(self.camera.start_of_capture, time.time()))

        try:
            self.capture = cv2.VideoCapture(self.camera.source)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera.height)
            self.capture.set(cv2.CAP_PROP_FPS, self.camera.fps)
            self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            self.capture.set(cv2.CAP_PROP_EXPOSURE, -8)
            snapshot_time = time.time()
            frame_number = 0

            frames_to_skip = self.camera.frames_to_skip

            while True:
                with self.capture_lock:
                    if not self.capturing:
                        break
                # Wait for the next time trigger
                while time.time() - snapshot_time <= 1 / self.camera.fps:
                    pass

                # Delay video capturing, if that's what's requested
                if frames_to_skip > 0:
                    self.capture.grab()
                    frames_to_skip -= 1
                    pass
                else:
                    frame_number += 1
                    if frame_number > self.camera.fps + 1 or int(time.time()) > int(snapshot_time):
                        frame_number = 1

                    snapshot_time = time.time()

                    grabbed = self.capture.grab()
                    if grabbed:
                        # Get the file path that will be used for the frame
                        file_path = SharedFunctions.get_recording_file_path(
                            self.camera.targetPath,
                            int(snapshot_time),
                            frame_number
                        )
                        filename = SharedFunctions.get_recording_file_name(int(snapshot_time),
                                                                           frame_number)
                        ref, frame = self.capture.retrieve(flag=0)

                        captured_frame = CapturedFrame(self.camera,
                                                       file_path,
                                                       filename,
                                                       frame_number,
                                                       snapshot_time,
                                                       frame_number % self.detection_frequency == 1,
                                                       frame)

                        self.ai_queue.enqueue(captured_frame, "AI Queue {}".format(self.camera.id))
        except cv2.error as e:
            self.capturing = False
            self.logger.error("Camera {}, on playground {} is not responding."
                              .format(self.camera.id, self.camera.playground))
        finally:
            self.ai_queue.mark_as_done()
            print("Camera {}, on playground {} finished recording."
                  .format(self.camera.id, self.camera.playground))

    def cv2error(self):
        self.logger.error("Camera {}, on playground {} is not responding."
                          .format(self.camera.id, self.camera.playground))

    def clear_cv_from_memory(self):
        if self.capture is not None:
            self.capture.release()
        cv2.waitKey(1)
        cv2.destroyAllWindows()
        for i in range(1, 5):
            cv2.waitKey(1)
