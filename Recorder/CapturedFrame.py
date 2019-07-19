import cv2
import threading


class CapturedFrame(object):
    def __init__(self, frame, file_path, queue, frame_number):
        self.frame = frame
        self.filePath = file_path
        self.queue = queue
        self.frame_number = frame_number

    def save_file_async(self):
        single_thread = threading.Thread(target=self.save_file, args=())
        single_thread.start()
        return single_thread

    def save_file(self):
        image = cv2.UMat(self.frame)
        cv2.imwrite(self.filePath, image)

        if self.frame_number % 30 == 1:
            self.queue.put(self.frame)
