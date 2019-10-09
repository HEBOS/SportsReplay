#!/usr/bin/env python3
import time


class Camera(object):
    def __init__(self, camera_id: int, source: str, fps: int, cdfps: float, width: int, height: int, playground: int,
                 session_path: str, planned_start_time: time, start_of_capture: time, end_of_capture: time):
        self.id = camera_id
        self.source = source
        self.fps = fps
        self.cdfps = cdfps
        self.width = width
        self.height = height
        self.playground = playground
        self.session_path = session_path
        self.planned_start_time = planned_start_time
        self.start_of_capture = start_of_capture
        self.end_of_capture = end_of_capture
        self.last_detection = time.time()
