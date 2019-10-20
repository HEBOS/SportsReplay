#!/usr/bin/env python3
from typing import List
from Shared.Detection import Detection
from Shared.SharedFunctions import SharedFunctions
from Polygon import Polygon
from Shared.Point import Point
import json


class DefinedPolygon(object):
    def __init__(self, camera: int, detect: bool, points: List[Point]):
        self.camera_id = camera
        self.points = points
        self.detect = detect
        self.polygon = Polygon(SharedFunctions.get_points_array(points))

    def contains_ball(self, ball: Detection) -> bool:
        return self.polygon.overlaps(ball.polygon)

    @staticmethod
    def get_polygons(json_content: str):
        json_obj = json.loads(json_content)
        polygons: List[DefinedPolygon] = []
        for p in json_obj:
            points: List[Point] = []
            for point in p["points"]:
                points.append(Point(point["x"], point["y"]))
            polygons.append(DefinedPolygon(p["camera"], p["detect"], points))
        return polygons

