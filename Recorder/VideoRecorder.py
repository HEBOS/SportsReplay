import os
import queue
import threading
import time
import logging
import shutil
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

        self.read_lock = threading.Lock()

        self.firstFrame = None
        self.repairing_frame = None
        self.lastRecordedFrame = None

        self.frameProcessingStop = False
        self.frameProcessingThread = threading.Thread(target=self.process_frames, args=())
        self.frameProcessingThread.start()

        self.frameCleanupStop = False
        self.frameCleanupThread = threading.Thread(target=self.cleanup, args=())
        self.frameCleanupThread.start()

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

    def read_frame(self, current_time):
        try:
            ret, image = self.capture.read()
            if ret:
                frame_number = int(round((current_time - int(current_time)) * self.fps, 1)) + 1

                if self.firstFrame is None:
                    self.firstFrame = (int(current_time), frame_number)

                self.lastRecordedFrame = (int(current_time), frame_number)

                file_path = os.path.normpath(
                    r"{target_path}/camera_{camera_number}_frame_{currentTime}_{frameNumber}.png"
                        .format(target_path=self.target_path,
                                camera_number=self.camera_number,
                                currentTime=int(current_time),
                                frameNumber=str(frame_number).zfill(4)))

            if not self.frameQueue.full():
                self.frameQueue.put_nowait(CapturedFrame(image, file_path))
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
                    current_time = time.time()
                    current_snapshot = int(current_time) + ((int(round((current_time - int(current_time)) *
                                                                       self.fps, 1)) + 1) / 10000)

                    if current_snapshot != previous_snapshot:
                        previous_snapshot = int(current_time) + \
                                            ((int(round((current_time - int(current_time)) * self.fps, 1)) + 1) / 10000)
                        read_thread = threading.Thread(target=self.read_frame, args=(time.time(),))
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
            self.frameProcessingStop = True
            self.frameCleanupStop = True
            self.frameCleanupThread.join()

    # Finishes the video recording therefore the thread too
    def stop(self):
        self.frameProcessingStop = True
        self.frameProcessingThread.join()
        if self.casting:
            self.casting = False
        else:
            pass

        self.frameCleanupStop = True
        self.frameCleanupThread.join()

        self.logger.warning('Recording with camera {}, on playground {} has been forcibly interrupted.'
                            .format(self.camera_number, self.playground))

    def cleanup(self):

        # Wait until first frame is captured
        while not self.frameCleanupStop:
            if self.firstFrame is not None:
                break

        # Wait 3 more seconds (to allow all threads to complete work)
        time.sleep(3)

        # Every second raise repair algorithm for the one second period (iterations = fps)
        try:
            if self.repairing_frame is None:
                self.repairing_frame = self.firstFrame

            while (not self.frameCleanupStop) or \
                    self.lastRecordedFrame[0] > self.repairing_frame[0] or \
                    (self.lastRecordedFrame[0] == self.repairing_frame[0] and
                     self.lastRecordedFrame[1] + 1 > self.repairing_frame[1]):

                # Get the next frame that needs to be checked
                previous_frame = self.repairing_frame
                self.repairing_frame = (self.repairing_frame[0] + 1, 1) \
                    if self.repairing_frame[1] == 31 \
                    else (self.repairing_frame[0], self.repairing_frame[1] + 1)

                # Repair next (fps) number of frames
                for i in range(1, self.fps + 1):
                    previous_file = os.path.normpath(
                        r"{target_path}/camera_{camera_number}_frame_{currentTime}_{frameNumber}.png"
                            .format(target_path=self.target_path,
                                    camera_number=self.camera_number,
                                    currentTime=previous_frame[0],
                                    frameNumber=str(previous_frame[1]).zfill(4)))
                    expected_file = os.path.normpath(
                        r"{target_path}/camera_{camera_number}_frame_{currentTime}_{frameNumber}.png"
                            .format(target_path=self.target_path,
                                    camera_number=self.camera_number,
                                    currentTime=self.repairing_frame[0],
                                    frameNumber=str(self.repairing_frame[1]).zfill(4)))

                    with self.read_lock:
                        if not os.path.isfile(expected_file):
                            # print("Compensating missing file {} by using {}".format(expected_file, previous_file))
                            shutil.copyfile(previous_file, expected_file)
                        else:
                            break

                # Wait for the next iteration
                current_time = time.time()
                while int(round((current_time - int(current_time)) * self.fps, 1)) + 1 != 1:
                    current_time = time.time()
        except Exception as ex:
            self.logger.error("Error fixing missing frames."
                              .format(self.camera_number, self.playground))

    def cv2error(self):
        self.logger.error("Camera {}, on playground {} is not responding."
                          .format(self.camera_number, self.playground))
