#!/usr/bin/env python3
import json
import cv2
import time
import os
from Shared.SharedFunctions import SharedFunctions
import Shared.Camera as Camera


class CapturedFrame(object):
    def __init__(self, camera: Camera, file_path: str, filename: str,
                 frame_number: int, snapshot_time: time, detect_candidate: bool):
        self.camera = camera
        self.filePath = file_path
        self.filename = filename
        self.frame_number = frame_number
        self.timestamp = int(snapshot_time) + float(frame_number / 1000)
        self.json = None
        self.snapshot_time = snapshot_time
        self.detect_candidate = detect_candidate
        self.largest_ball_size = 0

    def remove_file(self):
        if os.path.isfile(self.filePath):
            os.remove(self.filePath)

#class VRow(object):
#    def __init__(self, snapshot_time: time, frame_number: int, detect_candidate: bool):
