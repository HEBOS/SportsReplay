from typing import List
from Shared.Detection import Detection

class SquareGraph(object):
    def __init__(self, camera_id: int, top: int, right: int, bottom: int, left: int):
        self.camera_id = camera_id
        self.top = top
        self.right = right
        self.bottom = bottom
        self.left = left

    def contains_ball(self, ball: Detection):
        if ball.camera_id != self.camera_id:
            return False
        return ball.top >= self.top and ball.right <= self.right and \
               ball.bottom <= self.bottom and ball.left >= self.left

    @staticmethod
    def get_graphs(json_graphs):
        graphs: List[SquareGraph] = []
        for graph in json_graphs:
            graphs.append(SquareGraph(graph["camera_id"], graph["top"], graph["right"], graph["bottom"], graph["left"]))
        return graphs
