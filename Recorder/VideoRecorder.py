#!/usr/bin/env python3
import threading
import time
import logging
import cv2
import jetson.inference
import jetson.utils
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

        # Redirect OpenCV errors
        cv2.redirectError = self.cv2error

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
                self.capture = jetson.utils.gstCamera(self.camera.width, self.camera.height, self.camera.source)
                write_tasks = []
                snapshot_time = time.time()
                frame_number = 0

                while self.capturing:
                    # Wait for the next time trigger
                    while time.time() - snapshot_time <= 1 / self.camera.fps:
                        pass

                    # Delay video capturing, if that's what's requested
                    frame_number += 1
                    if frame_number > self.camera.fps + 1 or int(time.time()) > int(snapshot_time):
                        frame_number = 1

                    snapshot_time = time.time()

                    frame, width, height = self.capture.CaptureRGBA()
                    if frame:
                        # Get the file path that will be used for the frame
                        file_path = SharedFunctions.get_recording_file_path(
                            self.camera.targetPath,
                            int(snapshot_time),
                            frame_number
                        )
                        filename = SharedFunctions.get_recording_file_name(int(snapshot_time),
                                                                           frame_number)
                        captured_frame = CapturedFrame(self.camera,
                                                       frame,
                                                       file_path,
                                                       filename,
                                                       frame_number)
                        if captured_frame.frame_number % self.camera.fps == 1:
                            self.ai_queue.put_nowait(captured_frame)

                        frame_read_task = executor.submit(captured_frame.save_file)
                        write_tasks.append(frame_read_task)

            except cv2.Error.error as e:
                self.capturing = False
                self.logger.error("Camera {}, on playground {} is not responding."
                                  .format(self.camera.id, self.camera.playground))
            finally:
                self.stop_ai()
                if self.capture is not None:
                    self.capture.Close()
                concurrent.futures.wait(fs=write_tasks, timeout=10, return_when="ALL_COMPLETED")
                cv2.destroyAllWindows()

    def stop_ai(self):
        # putting poison pill in ai_queue
        self.ai_queue.put_nowait(None)

    # Finishes the video recording therefore the thread too
    def stop(self):
        self.stop_ai()

        if self.capturing:
            self.capturing = False
        else:
            pass

        self.logger.warning('Recording with camera {}, on playground {} has been forcibly interrupted.'
                            .format(self.camera.id, self.camera.playground))

    def cv2error(self):
        self.logger.error("Camera {}, on playground {} is not responding."
                          .format(self.camera.id, self.camera.playground))
