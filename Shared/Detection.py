#!/usr/bin/env python3
import time
from Shared.Point import Point
from Shared.SharedFunctions import SharedFunctions
from Polygon import Polygon
from typing import List


class Detection(object):
    def __init__(self, left: int, right: int, top: int, bottom: int, width: int, height: int,
                 confidence: float, instance: int, camera_id: int):
        self.camera_id = camera_id
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.width = width
        self.height = height
        self.confidence = confidence
        self.instance = instance
        self.ball_size = 2 * (self.width + self. height)
        self.recorded_time = time.time()
        points: List[Point] = [Point(self.left, self.top),
                               Point(self.left, self.bottom),
                               Point(self.right, self.top),
                               Point(self.right, self.bottom)]
        self.polygon = Polygon(SharedFunctions.get_points_array(points))
