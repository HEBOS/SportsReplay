#!/usr/bin/env python3
import time


class Camera(object):
    def __init__(self, camera_id: int, source: str, fps: int, cdfps: float, width: int, height: int, client: int,
                 building: int, playground: int, target_path: str, start_of_capture: time, end_of_capture: time):
        self.id = camera_id
        self.source = source
        self.fps = fps
        self.cdfps = cdfps
        self.width = width
        self.height = height
        self.client = client
        self.building = building
        self.playground = playground
        self.targetPath = target_path
        self.start_of_capture = start_of_capture
        self.end_of_capture = end_of_capture
        self.largest_ball_size = 0
        self.last_detection = time.time()
