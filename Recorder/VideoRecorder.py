import os
import queue
import threading
import time
import logging

import cv2

from Recorder.CapturedFrame import CapturedFrame
from Recorder.VideoCaptureAsync import VideoCaptureAsync
from Shared.LogHandler import LogHandler

class VideoRecorder(object):
    def __init__(self, camera_number, video_source, target_path, fps,
                 scheduled_end_of_recording, client, playground):
        # Redirect OpenCV errors
        cv2.redirectError(self.cv2error)

        self.client = client
        self.playground = playground
        self.casting = True
        self.video_source = video_source
        self.camera_number = camera_number
        self.target_path = target_path
        self.scheduled_end_of_recording = scheduled_end_of_recording

        # Fixed settings
        self.fps = fps
        self.frameSize = (1280, 720)
        self.frameQueue = queue.Queue(maxsize=10000)

        self.logger = LogHandler("recording")
        self.logger.info('Camera {}, on playground {} has started recording.'.format(camera_number, playground))

        self.frameProcessingStop = False
        self.frameProcessingThread = threading.Thread(target=self.process_frames, args=())
        self.frameProcessingThread.start()
        self.capture = VideoCaptureAsync(self.video_source,
                                         self.frameSize[0],
                                         self.frameSize[1],
                                         self.fps)
        self.frameProcessingThreads = []

    def process_frames(self):
        while (not self.frameProcessingStop) or (not self.frameQueue.empty()):
            if not self.frameQueue.empty():
                frame = self.frameQueue.get()
                self.frameProcessingThreads.append(frame.save_file_async())
        # Ensure all threads have finished their job
        for t in self.frameProcessingThreads:
            t.join()

    def read_frame(self):
        try:
            ret, image = self.capture.read()
            if ret:
                current_time = time.time()
                frame_number = int(round((((current_time - int(current_time)) / 100) * self.fps) * 100, 1)) + 1

                file_path = os.path.normpath(
                    r"{target_path}/camera_{camera_number}_frame_{currentTime}_{frameNumber}.png"
                    .format(target_path=self.target_path,
                            camera_number=self.camera_number,
                            currentTime=int(current_time),
                            frameNumber=str(frame_number).zfill(4)))

            if not self.frameQueue.full():
                self.frameQueue.put_nowait(CapturedFrame(image,
                                                         file_path,
                                                         self.camera_number,
                                                         self.fps,
                                                         int(current_time),
                                                         frame_number,
                                                         self.target_path))
        except Exception as ex:
            self.logger.error("Camera {}, on playground {} is not responding."
                              .format(self.camera_number, self.playground))
        finally:
            pass

    def record(self):
        try:
            self.casting = True
            try:
                previous_snapshot = 0
                self.capture.start()

                while time.time() < self.scheduled_end_of_recording and self.casting:
                    time_elapsed = time.time() - previous_snapshot

                    if time_elapsed >= (1. / self.fps):
                        previous_snapshot = time.time()
                        read_thread = threading.Thread(target=self.read_frame, args=())
                        read_thread.start()
            except Exception as ex:
                self.logger.error("Camera {}, on playground {} is not responding."
                                  .format(self.camera_number, self.playground))
            finally:
                self.capture.stop()
                cv2.destroyAllWindows()
            self.logger.info('Camera {}, on playground {} has finished recording successfully.'
                             .format(self.camera_number, self.playground))
        finally:
            self.frameProcessingStop = True
            self.frameProcessingThread.join()
            self.casting = False

    # Finishes the video recording therefore the thread too
    def stop(self):
        self.frameProcessingStop = True
        self.frameProcessingThread.join()
        if self.casting:
            self.casting = False
        else:
            pass

        self.logger.warning('Recording with camera {}, on playground {} has been forcibly interrupted.'
                        .format(self.camera_number, self.playground))

    def cv2error(self):
        self.logger.error("Camera {}, on playground {} is not responding."
                      .format(self.camera_number, self.playground))
