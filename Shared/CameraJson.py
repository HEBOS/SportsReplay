#!/usr/bin/env python3
import json
from typing import List
from Shared.SharedFunctions import SharedFunctions


class CameraJson(object):
    def __init__(self, camera_id: int, json_file_path: str):
        self.camera_id = camera_id
        self.json_file_path = json_file_path

    def get_ball_size(self) -> int:
        ball_sizes: List[int] = [0]
        try:
            with open(self.json_file_path) as json_file:
                data = json.load(json_file)
                if len(data) > 1:
                    print("There are {} balls detected.".format(len(data)))

                for ball in data:
                    x0 = ball["x0"]
                    x1 = ball["x1"]
                    y0 = ball["y0"]
                    y1 = ball["y1"]
                    a = x1 - x0
                    b = y1 - y0
                    ball_sizes.append(2 * (a + b))
            return max(ball_sizes)
        except:
            return 0

    def get_time(self) -> float:
        return float(SharedFunctions.get_time_from_file(self.json_file_path))
