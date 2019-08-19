#!/usr/bin/env python3
import multiprocessing as mp
from Shared.CapturedFrame import CapturedFrame
import cv2
import gc


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
        # out = cv2.VideoWriter(self.output_video, cv2.VideoWriter_fourcc(*'mp4v'), self.fps, (self.width, self.height))
        out = cv2.VideoWriter(self.output_video, cv2.VideoWriter_fourcc(*'mp4v'), self.fps, (self.width, self.height))

        i = 0
        while True:
            i += 1
            if not self.video_queue.empty():
                capture_frame: CapturedFrame = self.video_queue.get()

                if capture_frame is None:
                    break
                else:
                    frame = cv2.UMat(cv2.imread(capture_frame.filePath), usageFlags=cv2.USAGE_ALLOCATE_DEVICE_MEMORY)
                    out.write(frame)
                    cv2.waitKey(1)
                    del frame
                    capture_frame.remove_file()
                    if i % 20:
                        gc.collect()
                        i = 0
        out.release()
        self.clear_cv_from_memory()
        print("VideoMaker ended.")

    def clear_cv_from_memory(self):
        cv2.waitKey(1)
        cv2.destroyAllWindows()
        for i in range(1, 5):
            cv2.waitKey(1)
