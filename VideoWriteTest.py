#!/usr/bin/env python3
import os
import time
import cv2
import gc
import queue
import jetson.utils
from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions


class VideoWriteTest(object):
    def __init__(self):
        config = Configuration()
        fps = int(config.recorder["fps"])
        width = int(config.recorder["width"])
        height = int(config.recorder["height"])
        video_addresses = str(config.recorder["video"]).split(",")

        # Ensure that root directory exists
        dump_path = os.path.normpath(r"{}".format(config.common["dump-path"]))
        SharedFunctions.ensure_directory_exists(dump_path)

        # Ensure that video making directory exists
        video_making_path = os.path.join(dump_path, config.video_maker["video-making-path"])
        SharedFunctions.ensure_directory_exists(video_making_path)

        input_pipeline = "filesrc location={location} " \
                         "! qtdemux " \
                         "! h264parse " \
                         "! omxh264dec " \
                         "! nvvidconv " \
                         "! video/x-raw,format=RGBA,width={width},height={height},framerate={fps}/1 " \
                         "! videoconvert " \
                         "! appsink".format(location=os.path.normpath(r"{}".format(video_addresses[0])),
                                            fps=fps,
                                            width=width,
                                            height=height)

        output_pipeline = "appsrc " \
                          "! autovideoconvert " \
                          "! video/x-raw,width={width},height={height},framerate={fps}/1 " \
                          "! omxh264enc " \
                          "! video/x-h264,stream-format=byte-stream " \
                          "! h264parse " \
                          "! qtmux " \
                          "! filesink location={video}".format(width=width,
                                                               height=height,
                                                               fps=fps,
                                                               video="output.mp4v")
        print("VideoCapture:")
        print("-----------------------------------------------------------------------------------------------")
        print(input_pipeline)
        capture = cv2.VideoCapture(input_pipeline, cv2.CAP_GSTREAMER)
        print("")
        print("")
        print("VideoWriter:")
        print(output_pipeline)
        print("-----------------------------------------------------------------------------------------------")
        writer = cv2.VideoWriter(output_pipeline, cv2.VideoWriter_fourcc(*'MP4V'), fps, (width, height), True)

        q = queue.Queue(maxsize=10000)
        started_at = time.time()
        while time.time() - started_at < 10:
            grabbed, img = capture.read()
            if grabbed:
                cv2.waitKey(1)
                q.put(img)

        started_at = time.time()
        i = 0
        while True:
            i += 1
            writer.write(q.get())
            if i >= 250:
                break

        print("Write utilisation equals {} fps.".format((time.time() - started_at) / 250))

        capture.release()
        writer.release()

        self.clear_cv_from_memory()
        gc.collect()

    def clear_cv_from_memory(self):
        cv2.waitKey(1)
        cv2.destroyAllWindows()
        for i in range(1, 5):
            cv2.waitKey(1)


if __name__ == "__main__":
    st = VideoWriteTest()
