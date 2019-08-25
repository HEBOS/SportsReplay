#!/usr/bin/env python3
import cv2
import gc
import os
from Shared.CapturedFrame import CapturedFrame
from Shared.SharedFunctions import SharedFunctions
from Shared.MultiProcessingQueue import MultiProcessingQueue


class VideoMaker(object):
    def __init__(self, playground: int, video_queue: MultiProcessingQueue, output_video: str,
                 width: int, height: int, fps: int):
        self.playground = playground
        self.video_queue = video_queue
        self.output_video = output_video
        self.width = width
        self.height = height
        self.fps = fps
        self.video_creating = False

    def start(self):
        self.video_creating = True
        writer = None

        i = 0
        while True:
            if not self.video_queue.is_empty():
                if writer is None:
                    output_pipeline = "appsrc " \
                                      "! autovideoconvert " \
                                      "! video/x-raw,width={width},height={height},framerate={fps}/1 " \
                                      "! omxh264enc ! video/x-h264,stream-format=byte-stream " \
                                      "! h264parse " \
                                      "! qtmux " \
                                      "! filesink location={video}".format(width=self.width,
                                                                           height=self.height,
                                                                           fps=self.fps,
                                                                           video=self.output_video)

                    writer = cv2.VideoWriter(output_pipeline,
                                             cv2.VideoWriter_fourcc(*'mp4v'),
                                             self.fps,
                                             (self.width, self.height),
                                             True)

                i += 1
                capture_frame: CapturedFrame = self.video_queue.dequeue("Video Queue")

                if capture_frame is None:
                    break
                else:
                    if capture_frame.frame is None:
                        print("FRAME JE EMPTYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY")
                    writer.write(capture_frame.frame)
                    capture_frame.release()
                    del capture_frame

                    if i % self.fps == 0:
                        print("Output video: {}. Frames written {}".format(
                            SharedFunctions.normalise_time(i, self.fps), i))
        writer.release()
        SharedFunctions.release_open_cv()
        print("VideoMaker ended.")

