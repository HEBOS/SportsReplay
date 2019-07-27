import threading
import time
import logging
import cv2

from Recorder.VideoCaptureAsync import VideoCaptureAsync
from Shared.LogHandler import LogHandler
from Shared.SharedFunctions import SharedFunctions
from Shared.Camera import Camera


class VideoRecorder(object):
    def __init__(self, camera: Camera):
        self.camera = camera

        # Redirect OpenCV errors
        cv2.redirectError(self.cv2error)

        self.casting = True
        self.logger = LogHandler("recording")
        self.logger.info('Camera {}, on playground {} has started recording.'.format(camera.id, camera.playground))

        self.read_lock = threading.Lock()
        self.frameProcessingStop = False

        self.capture = VideoCaptureAsync(self.camera)

    def record(self):
        try:
            # Sync the start with other cameras, so they start at the same time
            while time.time() < self.camera.start_of_capture and not self.frameProcessingStop:
                time.sleep(.010)

            self.casting = True
            self.capture.start()
            print("Starting at {}".format(self.camera.start_of_capture))
            while (time.time() < self.camera.end_of_capture) and self.casting:
                time.sleep(.010)
        except Exception as ex:
            print(ex)
            self.logger.error("Camera {}, on playground {} is not responding."
                              .format(self.camera.id, self.camera.playground))
        finally:
            print("Ending at {}".format(self.camera.end_of_capture))
            self.capture.stop()
            self.frameProcessingStop = True
            self.frameProcessingStop = True

    # Finishes the video recording therefore the thread too
    def stop(self):
        # putting poison pill in ai_queue
        self.camera.aiQueue.put_nowait(None)

        self.frameProcessingStop = True
        if self.casting:
            self.casting = False
        else:
            pass

        self.logger.warning('Recording with camera {}, on playground {} has been forcibly interrupted.'
                            .format(self.camera.id, self.camera.playground))

    def cv2error(self):
        self.logger.error("Camera {}, on playground {} is not responding."
                          .format(self.camera.id, self.camera.playground))
