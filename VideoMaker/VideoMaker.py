#!/usr/bin/env python3
import cv2
import gc
from Shared.CapturedFrame import CapturedFrame
from Shared.SharedFunctions import SharedFunctions
from Shared.MultiProcessingQueue import MultiProcessingQueue


class VideoMaker(object):
    def __init__(self, playground: int, video_queue: MultiProcessingQueue, output_video: str,
                 width: int, height: int, fps: int, debugging: bool):
        self.playground = playground
        self.video_queue = video_queue
        self.output_video = output_video
        self.width = width
        self.height = height
        self.debugging = debugging
        self.fps = fps
        self.video_creating = False

    def start(self):
        self.video_creating = True
        output_pipeline = "appsrc " \
                          "! autovideoconvert " \
                          "! video/x-raw,width={width},height={height},format=I420,framerate={fps}/1 " \
                          "! omxh264enc " \
                          "! video/x-h264,stream-format=byte-stream " \
                          "! h264parse " \
                          "! qtmux " \
                          "! filesink location={video}{space}".format(width=self.width,
                                                                      height=self.height,
                                                                      fps=self.fps,
                                                                      video=self.output_video,
                                                                      space=" ")
        print(output_pipeline)
        writer = cv2.VideoWriter(output_pipeline,
                                 cv2.VideoWriter_fourcc(*'mp4v'),
                                 self.fps,
                                 (self.width, self.height),
                                 True)
        i = 0
        while True:
            if not self.video_queue.is_empty():
                i += 1
                captured_frame: CapturedFrame = self.video_queue.dequeue("Video Queue")

                if captured_frame is None:
                    break
                else:
                    writer.write(captured_frame.frame)
                    captured_frame.release()

                    if i % self.fps == 0:
                        print("Output video: {}. Frames written {}".format(
                            SharedFunctions.normalise_time(i, self.fps), i))
                        gc.collect()

        writer.release()
        SharedFunctions.release_open_cv()
        print("VideoMaker ended.")

