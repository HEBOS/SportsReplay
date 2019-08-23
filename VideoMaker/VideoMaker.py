#!/usr/bin/env python3
import multiprocessing as mp
import cv2
import gc
import os
from Shared.CapturedFrame import CapturedFrame
from Shared.SharedFunctions import SharedFunctions


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
        output_pipeline = "appsrc " \
                          "! autovideoconvert " \
                          "! video/x-raw,format=(string)I420,width={width},height={height},framerate={fps}/1 " \
                          "! omxh264enc ! video/x-h264,stream-format=(string)byte-stream " \
                          "! h264parse " \
                          "! qtmux " \
                          "! filesink location={video}.avi".format(width=self.width,
                                                                   height=self.height,
                                                                   fps=self.fps,
                                                                   video=self.output_video)

        writer = cv2.VideoWriter(output_pipeline, cv2.VideoWriter_fourcc(*'X264'), self.fps, (self.width, self.height))

        i = 0
        while True:
            i += 1
            if not self.video_queue.empty():
                capture_frame: CapturedFrame = self.video_queue.get()

                if capture_frame is None:
                    break
                else:
                    writer.write(capture_frame.frame)
                    capture_frame.release()
                    if i % self.fps == 0:
                        print("Output video: {}".format(SharedFunctions.normalise_time(i, self.fps)))
        writer.release()
        self.clear_cv_from_memory()
        print("VideoMaker ended.")

    def clear_cv_from_memory(self):
        cv2.waitKey(1)
        cv2.destroyAllWindows()
        for i in range(1, 5):
            cv2.waitKey(1)
