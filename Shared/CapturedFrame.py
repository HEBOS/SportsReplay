#!/usr/bin/env python3
import time
import Shared.Camera as Camera
import numpy as np


class CapturedFrame(object):
    def __init__(self, camera: Camera, frame_number: int, snapshot_time: time, frame: np.array, camera_time: time):
        self.camera = camera
        self.frame_number = frame_number
        self.timestamp = int(snapshot_time) + float(frame_number / 1000)
        self.snapshot_time = snapshot_time
        self.frame = frame
        self.camera_time = camera_time

    def release(self):
        self.frame = None
