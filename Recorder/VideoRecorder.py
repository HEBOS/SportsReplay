import threading
import time
import logging
import cv2
import concurrent.futures
from Shared.LogHandler import LogHandler
from Shared.SharedFunctions import SharedFunctions
from Shared.Camera import Camera
from Shared.CapturedFrame import CapturedFrame


class VideoRecorder(object):
    def __init__(self, camera: Camera):
        self.camera = camera

        # Redirect OpenCV errors
        cv2.redirectError(self.cv2error)

        # Logger
        self.logger = LogHandler("recording")
        self.logger.info('Camera {}, on playground {} has started recording.'.format(camera.id, camera.playground))

        # Capturing support
        self.capture = None
        self.capturing = True
        self.captureThread = None
        self.frameReadTasks = []

        # Logger support
        self.logger = LogHandler("recording")

    def start(self):
        try:
            self.capturing = True
            self.captureThread = threading.Thread(target=self.record, args=())
            self.captureThread.start()

            # print("Starting at {}".format(self.camera.start_of_capture))

            while (time.time() < self.camera.end_of_capture) and self.capturing:
                time.sleep(1)
        except Exception as ex:
            print(ex)
            self.logger.error("Camera {}, on playground {} is not responding."
                              .format(self.camera.id, self.camera.playground))
        finally:
            print("Expected ending {}. Ending at {}".format(self.camera.end_of_capture, time.time()))
            self.capturing = False
            self.captureThread.join()

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

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                snapshot_time = time.time()
                frame_number = 0

                while self.capturing:
                    # Wait for the next time trigger
                    while time.time() - snapshot_time <= 1 / self.camera.fps:
                        pass

                    snapshot_time = time.time()
                    frame_number += 1
                    if frame_number > self.camera.fps + 1:
                        frame_number = 1

                    grabbed = self.capture.grab()
                    if grabbed:
                        # Get the file path that will be used for the frame
                        file_path = SharedFunctions.get_recording_file_path(
                            self.camera.targetPath,
                            self.camera.id,
                            int(snapshot_time),
                            frame_number
                        )
                        filename = SharedFunctions.get_recording_file_name(self.camera.id,
                                                                           int(snapshot_time),
                                                                           frame_number)
                        ref, frame = self.capture.retrieve(flag=0)
                        cv2.waitKey(1)
                        captured_frame = CapturedFrame(self.camera,
                                                       frame,
                                                       file_path, filename,
                                                       frame_number)
                        frame_read_task = executor.submit(self.save_captured_file, captured_frame)
                        self.frameReadTasks.append(frame_read_task)
                concurrent.futures.wait(fs=self.frameReadTasks, return_when="ALL_COMPLETED")
        except cv2.error as e:
            self.logger.error("Camera {}, on playground {} is not responding."
                              .format(self.camera.id, self.camera.playground))
        finally:
            if self.capture is not None:
                self.capture.release()
            cv2.destroyAllWindows()
            self.capturing = False

    def save_captured_file(self, captured_frame: CapturedFrame):
        cv2.imwrite(captured_frame.filePath, captured_frame.frame)

    # Finishes the video recording therefore the thread too
    def stop(self):
        # putting poison pill in ai_queue
        self.camera.aiQueue.put_nowait(None)

        if self.capturing:
            self.capturing = False
        else:
            pass

        self.logger.warning('Recording with camera {}, on playground {} has been forcibly interrupted.'
                            .format(self.camera.id, self.camera.playground))

    def cv2error(self):
        self.logger.error("Camera {}, on playground {} is not responding."
                          .format(self.camera.id, self.camera.playground))
