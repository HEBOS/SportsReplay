#!/usr/bin/env python3
import json

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
        self.ball_size = self.get_ball_size()

    def get_ball_size(self) -> int:
        return 2 * (self.width + self. height)

