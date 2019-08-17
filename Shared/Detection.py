#!/usr/bin/env python3


class Detection(object):
    def __init__(self, left: int, right: int, top: int, bottom: int, width: int, height: int,
                 confidence: float, instance: int):
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.width = width
        self.height = height

    def get_ball_size(self) -> int:
        return 2 * (self.width + self. height)

