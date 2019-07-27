import os
import shutil
import threading
import cv2
import time
import concurrent.futures
from Shared.CapturedFrame import CapturedFrame
from Shared.LogHandler import LogHandler
from Shared.SharedFunctions import SharedFunctions
from Shared.Camera import Camera


class VideoCaptureAsync:
    def __init__(self, camera: Camera):
        self.camera = camera

        # Redirect OpenCV errors
        cv2.redirectError(self.cv2error)

        self.writeLock = threading.Lock()
        self.read_lock = threading.Lock()
        self.logger = LogHandler("recording")
        self.started = False
        self.thread = None
        self.cap = None
        self.firstFrame = None
        self.repairing_frame = None
        self.lastRecordedFrame = None
        self.frameCleanupStop = False
        self.frameCleanupThread = threading.Thread(target=self.cleanup, args=())
        self.frameCleanupThread.start()

    def start(self):
        if self.started:
            print("Recording is already started.")
        else:
            self.thread = threading.Thread(target=self.update, args=())
            self.cap = cv2.VideoCapture(self.camera.source)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.camera.fps)
            # self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            # self.cap.set(cv2.CAP_PROP_EXPOSURE, -8)
            with self.writeLock:
                self.started = True
            self.thread.start()

    def update(self):
        submitted_jobs = []
        try:
            snapshot_time = time.time()
            # Do until interrupted
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                while self.started:
                    # Wait for the next time trigger
                    while time.time() - snapshot_time <= 1 / self.camera.fps:
                        pass

                    # Submit new future, which will deal with reading a captured frame, to ThreadPoolExecutor
                    snapshot_time = time.time()
                    submitted_jobs.append(executor.submit(self.read_single_frame, snapshot_time))
                    # print("Duration: {}".format(time.time() - snapshot_time))
                concurrent.futures.wait(fs=submitted_jobs, return_when="ALL_COMPLETED")

        except cv2.error as e:
            self.started = False
            self.thread.join()
            self.logger.error("Camera {}, on playground {} is not responding."
                              .format(self.camera.id, self.camera.playground))
        finally:
            # Wait for all single_frame_threads' to complete
            cv2.destroyAllWindows()
            self.frameCleanupStop = True
            self.frameCleanupThread.join()

    def read_single_frame(self, snapshot_time):
        # Record a frame
        with self.read_lock:
            grabbed, frame = self.cap.read()
            if grabbed:
                fps_based_snapshot_time = int(snapshot_time) + \
                                          ((int(round((snapshot_time - int(snapshot_time)) *
                                                      self.camera.fps, 0)) + 1) / 10000)

                frame_number = int(round((fps_based_snapshot_time - int(fps_based_snapshot_time)) * 10000, 0))

                if self.firstFrame is None:
                    self.firstFrame = (int(snapshot_time), frame_number)

                self.lastRecordedFrame = (int(snapshot_time), frame_number)

                file_path = SharedFunctions.get_recording_file_path(
                    self.camera.targetPath,
                    self.camera.id,
                    int(snapshot_time),
                    frame_number
                )

                filename = SharedFunctions.get_recording_file_name(self.camera.id,
                                                                   int(fps_based_snapshot_time),
                                                                   frame_number)
                # self.camera.add_frame(CapturedFrame(self.camera, frame, file_path, filename, frame_number))
                cv2.imwrite(file_path, frame)

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
                    if self.repairing_frame[1] == self.camera.fps + 1 \
                    else (self.repairing_frame[0], self.repairing_frame[1] + 1)

                # Repair next (fps) number of frames
                for i in range(1, self.camera.fps + 1):
                    previous_file = SharedFunctions.get_recording_file_path(
                        self.camera.targetPath,
                        self.camera.id,
                        previous_frame[0],
                        previous_frame[1]
                    )

                    expected_file = SharedFunctions.get_recording_file_path(
                        self.camera.targetPath,
                        self.camera.id,
                        self.repairing_frame[0],
                        self.repairing_frame[1]
                    )

                    with self.read_lock:
                        if not os.path.isfile(expected_file):
                            # print("Compensating missing file {} by using {}".format(expected_file, previous_file))
                            shutil.copyfile(previous_file, expected_file)
                        else:
                            break

                # Wait for the next iteration
                current_time = time.time()
                while int(round((current_time - int(current_time)) * self.camera.fps, 1)) + 1 != 1:
                    current_time = time.time()
        except Exception as ex:
            print(ex)
            self.logger.error("Error fixing missing frames."
                              .format(self.camera.id, self.camera.playground))

    def stop(self):
        if not self.started:
            print("Recording is not started.")
        else:
            with self.writeLock:
                self.started = False
            self.thread.join()
            cv2.destroyAllWindows()

    def cv2error(self):
        self.logger.error("Camera {}, on playground {} is not responding."
                          .format(self.camera.id, self.camera.playground))

    def __exit__(self, exec_type, exc_value, traceback):
        self.cap.release()
