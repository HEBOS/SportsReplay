import cv2
import threading
import json
import numpy as np
import multiprocessing as mp
from Shared.SharedFunctions import SharedFunctions
import Shared.Camera as Camera


class CapturedFrame(object):
    def __init__(self, camera: Camera, frame: cv2.UMat, file_path: str, filename: str, frame_number: int):
        self.camera = camera
        self.frame = frame
        self.filePath = file_path
        self.filename = filename
        self.frame_number = frame_number
        self.json = None

    def save_file(self):
        cv2.imwrite(self.filePath, self.frame)

    def save_json(self):
        single_thread = threading.Thread(target=self.save_json_async(), args=())
        single_thread.start()
        return single_thread

    def save_json_async(self):
        json_file_path = SharedFunctions.get_json_file_path(self.filePath)
        print(json_file_path)
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.json, f, ensure_ascii=False, indent=4)
