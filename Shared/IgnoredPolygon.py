from typing import List
from Shared.Detection import Detection
from Shared.SharedFunctions import SharedFunctions
from Polygon import Polygon
from Shared.Point import Point
import json


class IgnoredPolygon(object):
    def __init__(self, camera: int, points: List[Point]):
        self.camera_id = camera
        self.points = points
        self.polygon = Polygon(SharedFunctions.get_points_array(points))

    def contains_ball(self, ball: Detection):
        return self.polygon.overlaps(ball.polygon)

    @staticmethod
    def get_polygons(json_content: str):
        json_obj = json.loads(json_content)
        polygons: List[IgnoredPolygon] = []
        for p in json_obj:
            points: List[Point] = []
            for point in p["points"]:
                points.append(Point(point["x"], point["y"]))
            polygons.append(IgnoredPolygon(p["camera"], points))
        return polygons

