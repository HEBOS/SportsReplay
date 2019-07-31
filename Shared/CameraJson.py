import json
from Shared.SharedFunctions import SharedFunctions


class CameraJson(object):
    def __init__(self, camera_id: int, json_file_path: str):
        self.camera_id = camera_id
        self.json_file_path = json_file_path

    def get_ball_size(self) -> int:
        try:
            with open(self.json_file_path) as json_file:
                data = json.load(json_file)
                if len(data) != 1:
                    return 0
                else:
                    ball = data[0]
                    x0 = ball["x0"]
                    x1 = ball["x1"]
                    y0 = ball["y0"]
                    y1 = ball["y1"]
                    a = x1 - x0
                    b = y1 - y0
                    return 2 * (a + b)
        except:
            return 0

    def get_time(self) -> str:
        return SharedFunctions.get_time_from_file(self.json_file_path)
