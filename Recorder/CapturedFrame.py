import cv2
import threading
import os
import shutil


class CapturedFrame(object):
    def __init__(self, frame, file_path, camera_number, fps, second, frame_number, target_path):
        self.frame = frame
        self.filePath = file_path
        self.fps = fps
        self.camera_number = camera_number
        self.second = second
        self.frame_number = frame_number
        self.target_path = target_path
        self.missing_shots = 0

    def save_file_async(self):
        single_thread = threading.Thread(target=self.save_file, args=())
        single_thread.start()
        return single_thread

    def ensure_previous_file_exist(self, given_second, given_frame_number):
        expected_second = given_second
        expected_frame_number = given_frame_number - 1

        if expected_frame_number == 0:
            expected_second = given_second - 1
            expected_frame_number = self.fps

        expected_file = os.path.normpath(
                    r"{target_path}/camera_{camera_number}_frame_{currentTime}_{frameNumber}.png"
                    .format(target_path=self.target_path,
                            camera_number=self.camera_number,
                            currentTime=int(expected_second),
                            frameNumber=str(expected_frame_number).zfill(4)))
        if not os.path.isfile(expected_file) and self.missing_shots <= 5:
            self.missing_shots += 1
            shutil.copyfile(self.filePath, expected_file)
            self.ensure_previous_file_exist(expected_second, expected_frame_number)

    def save_file(self):
        cv2.imwrite(self.filePath, self.frame)
        self.ensure_previous_file_exist(self.second, self.frame_number)
