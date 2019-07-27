import cv2
import threading
import json
import numpy as np
from Shared.SharedFunctions import SharedFunctions
import Shared.Camera as Camera


class CapturedFrame(object):
    def __init__(self, camera: Camera, frame, file_path: str, filename: str, frame_number: int):
        self.camera = camera
        self.frame = frame
        self.filePath = file_path
        self.filename = filename
        self.frame_number = frame_number
        self.json = None
        self.json_directory = None

    def save_file_async(self):
        single_thread = threading.Thread(target=self.save_file, args=())
        single_thread.start()
        return single_thread

    def save_file(self):
        image = np.float32(self.frame)
        cv2.imwrite(self.filePath, image)

        # if self.frame_number % self.camera.fps == 1:
        #    self.camera.aiQueue.put_nowait(self.frame)

    def save_json_async(self):
        single_thread = threading.Thread(target=self.save_json(), args=())
        single_thread.start()
        return single_thread

    def save_json(self):
        json_file_path = SharedFunctions.get_json_file_path(self.json, self.filename)
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.json, f, ensure_ascii=False, indent=4)
