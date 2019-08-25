#!/usr/bin/env python3
import time
import os
import Shared.Camera as Camera
import numpy
import gc


class CapturedFrame(object):
    def __init__(self, camera: Camera, file_path: str, filename: str,
                 frame_number: int, snapshot_time: time, detect_candidate: bool, frame: numpy.array):
        self.camera = camera
        self.filePath = file_path
        self.filename = filename
        self.frame_number = frame_number
        self.timestamp = int(snapshot_time) + float(frame_number / 1000)
        self.snapshot_time = snapshot_time
        self.detect_candidate = detect_candidate
        self.largest_ball_size = 0
        self.frame = frame

    def remove_file(self):
        if os.path.isfile(self.filePath):
            os.remove(self.filePath)

    def release(self):
        del self.frame
        if self.frame_number % (self.camera.fps * 2) == 0:
            gc.collect()

    def get_future_timestamp(self, frames_to_add: int):
        return int(self.snapshot_time) + int(frames_to_add / self.camera.fps) + \
               ((self.frame_number + (frames_to_add % self.camera.fps)) / 1000)
