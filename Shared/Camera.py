import multiprocessing as mp
import time
import queue
import Shared.CapturedFrame as CapturedFrame


class Camera(object):
    def __init__(self, camera_id: int, source: str, fps: int, width: int, height: int, client: int,
                 building: int, playground: int, target_path: str, start_of_capture: time, end_of_capture: time):
        self.id = camera_id
        self.source = source
        self.fps = fps
        self.width = width
        self.height = height
        self.client = client
        self.building = building
        self.playground = playground
        self.targetPath = target_path
        self.captureQueue = queue.Queue(maxsize=10000)
        self.aiQueue = mp.Queue(maxsize=10000)
        self.start_of_capture = start_of_capture
        self.end_of_capture = end_of_capture

    def add_frame(self, frame: CapturedFrame):
        self.captureQueue.put(frame)
