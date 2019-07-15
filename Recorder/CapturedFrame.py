import cv2
import threading


class CapturedFrame(object):
    def __init__(self, frame, file_path):
        self.frame = frame
        self.filePath = file_path

    def save_file_async(self):
        single_thread = threading.Thread(target=self.save_file, args=())
        single_thread.start()
        return single_thread

    def save_file(self):
        image = cv2.UMat(self.frame)
        cv2.imwrite(self.filePath, image)
