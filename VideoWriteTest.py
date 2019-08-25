#!/usr/bin/env python3
import os
import time
import cv2
import gc
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

        started_at = time.time()
        simg = cv2.imread("/home/sportsreplay/GitHub/sports-replay-hrvoje/ActivityDetector/SampleImages/frame_1564827634_0001.jpg")
        for i in range(0, 500):
            grabbed, img = capture.read()
            if grabbed:
                cv2.waitKey(1)
                rgba = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
                writer.write(img)
                cv2.imwrite("output.jpg", rgba)

        capture.release()
        writer.release()

        print("For 30 secs of video, at {} fps, it took {} secs to complete.".format(fps, time.time() - started_at))
        self.clear_cv_from_memory()
        gc.collect()

    def clear_cv_from_memory(self):
        cv2.waitKey(1)
        cv2.destroyAllWindows()
        for i in range(1, 5):
            cv2.waitKey(1)


if __name__ == "__main__":
    st = VideoWriteTest()
