#!/usr/bin/env python3
import multiprocessing as mp
from Shared.CapturedFrame import CapturedFrame
import cv2


class VideoMaker(object):
    def __init__(self, playground: int, video_queue: mp.Queue, output_video: str, width: int, height: int, fps: int):
        self.playground = playground
        self.video_queue = video_queue
        self.output_video = output_video
        self.width = width
        self.height = height
        self.fps = fps
        self.video_creating = False

    def start(self):
        self.video_creating = True
        out = cv2.VideoWriter(self.output_video, cv2.VideoWriter_fourcc(*'DIVX'), self.fps, (self.width, self.height))

        while True:
            if not self.video_queue.empty():
                capture_frame: CapturedFrame = self.video_queue.get()

                if capture_frame is None:
                    break
                else:
                    out.write(capture_frame.frame)

        out.release()
        print("VideoMaker ended.")
