#!/usr/bin/env python3
import time
from Shared.Point import Point
from Shared.SharedFunctions import SharedFunctions
from Polygon import Polygon
from typing import List


class Detection(object):
    def __init__(self, left: int, right: int, top: int, bottom: int, width: int, height: int,
                 confidence: float, camera_id: int, frame_number: float):
        self.camera_id = camera_id
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.width = width
        self.height = height
        self.confidence = confidence
        self.frame_number = frame_number
        self.points: List[Point] = [Point(self.left, self.top),
                                    Point(self.left, self.bottom),
                                    Point(self.right, self.bottom),
                                    Point(self.right, self.top)]

        self.polygon = Polygon(SharedFunctions.get_points_array(self.points))
