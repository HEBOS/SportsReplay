import threading
import time
import logging
import cv2
import concurrent.futures
import multiprocessing as mp
from Shared.LogHandler import LogHandler
from Shared.SharedFunctions import SharedFunctions
from Shared.Camera import Camera
from Shared.CapturedFrame import CapturedFrame


class VideoRecorder(object):
    def __init__(self, camera: Camera, ai_queue: mp.Queue):
        self.camera = camera
        self.ai_queue = ai_queue

        # Logger
        self.logger = LogHandler("recording")
        self.logger.info('Camera {}, on playground {} has started recording.'.format(camera.id, camera.playground))

        # Capturing support
        self.capture = None
        self.capturing = True
        self.captureThread = None

    def start(self):
        try:
            self.capturing = True
            self.captureThread = threading.Thread(target=self.record, args=())
            self.captureThread.start()

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

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            try:
                self.capture = cv2.VideoCapture(self.camera.source)
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera.width)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera.height)
                self.capture.set(cv2.CAP_PROP_FPS, self.camera.fps)
                self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
                self.capture.set(cv2.CAP_PROP_EXPOSURE, -8)
                write_tasks = []
                snapshot_time = time.time()
                frame_number = 0

                frames_to_skip = self.camera.frames_to_skip

                while self.capturing:
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
                            cv2.waitKey(1)

                            captured_frame = CapturedFrame(self.camera,
                                                           frame,
                                                           file_path,
                                                           filename,
                                                           frame_number,
                                                           snapshot_time)

                            if captured_frame.frame_number % self.camera.fps == 1:
                                self.ai_queue.put(captured_frame, block=True, timeout=2)

                            frame_read_task = executor.submit(captured_frame.save_file)
                            write_tasks.append(frame_read_task)

            except cv2.error as e:
                self.capturing = False
                self.logger.error("Camera {}, on playground {} is not responding."
                                  .format(self.camera.id, self.camera.playground))
            finally:
                self.stop_ai()
                if self.capture is not None:
                    self.capture.release()
                concurrent.futures.wait(fs=write_tasks, timeout=10, return_when="ALL_COMPLETED")

    def stop_ai(self):
        # putting poison pill in ai_queue
        self.ai_queue.put(None)

    def cv2error(self):
        self.logger.error("Camera {}, on playground {} is not responding."
                          .format(self.camera.id, self.camera.playground))
