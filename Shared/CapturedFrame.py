#!/usr/bin/env python3
import json
import cv2
import time
from Shared.SharedFunctions import SharedFunctions
import Shared.Camera as Camera


class CapturedFrame(object):
    def __init__(self, camera: Camera, frame, file_path: str, filename: str,
                 frame_number: int, snapshot_time: time):
        self.camera = camera
        self.frame = frame
        self.filePath = file_path
        self.filename = filename
        self.frame_number = frame_number
        self.json = None
        self.snapshot_time = snapshot_time

    def save_json(self):
        json_file_path = SharedFunctions.get_json_file_path(self.filePath)
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.json, f, ensure_ascii=False, indent=4)

    def save_file(self):
        cv2.imwrite(self.filePath, cv2.UMat(self.frame))
