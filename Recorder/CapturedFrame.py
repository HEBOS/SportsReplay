import cv2
import threading
import json

from Shared.SharedFunctions import SharedFunctions


class CapturedFrame(object):
    def __init__(self, frame, file_path, filename, queue, frame_number, fps):
        self.frame = frame
        self.filePath = file_path
        self.filename = filename
        self.queue = queue
        self.frame_number = frame_number
        self.fps = fps
        self.json = None
        self.json_directory = None

    def save_file_async(self):
        single_thread = threading.Thread(target=self.save_file, args=())
        single_thread.start()
        return single_thread

    def save_file(self):
        image = cv2.UMat(self.frame)
        cv2.imwrite(self.filePath, image)

        if self.frame_number % self.fps == 1:
            self.queue.put(self.frame)

    def save_json_async(self):
        single_thread = threading.Thread(target=self.save_json(), args=())
        single_thread.start()
        return single_thread

    def save_json(self):
        json_file_path = SharedFunctions.get_json_file_path(self.json, self.filename)
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.json, f, ensure_ascii=False, indent=4)
