#!/usr/bin/env python3
import os
import time
import cv2
import gc
import queue
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
                         "! queue " \
                         "! h264parse " \
                         "! omxh264dec " \
                         "! video/x-raw,format=NV12 " \
                         "! videoconvert " \
                         "! video/x-raw,format=BGR " \
                         "! appsink sync=0".format(location=os.path.normpath(r"{}".format(video_addresses[0])),
                                            fps=fps,
                                            width=width,
                                            height=height)

        #input_pipeline = input_pipeline.replace("(", "\\(").replace(")", "\\)")

        output_pipeline = "appsrc " \
                          "! videoconvert " \
                          "! video/x-raw,width=1280,height=720,framerate=25/1,format=I420 " \
                          "! omxh264enc " \
                          "! h264parse " \
                          "! qtmux " \
                          "! filesink location={video} ".format(video="output.mp4v",
                                                                fps=fps,
                                                                width=width,
                                                                height=height)

        output_pipeline = output_pipeline.replace("(", "\\(").replace(")", "\\)")
        print("VideoCapture:")
        print("-----------------------------------------------------------------------------------------------")
        print(input_pipeline)
        capture = cv2.VideoCapture(input_pipeline, cv2.CAP_GSTREAMER)

        q = queue.Queue(maxsize=1000)
        started_at = time.time()
        j = 0
        while time.time() - started_at < 10:
            j += 1
            grabbed, img = capture.read()
            if grabbed:
                try:
                    print("Grabbed {}".format(j))
                    q.put(img)
                except:
                    break

        print("")
        print("")
        print("VideoWriter:")
        print(output_pipeline)
        print("-----------------------------------------------------------------------------------------------")
        # cv2.VideoWriter_fourcc(*'H264'),

        writer = cv2.VideoWriter(output_pipeline, cv2.VideoWriter_fourcc(*'mp4v'),
                                 fps, (width, height), True)

        started_at = time.time()
        i = 0
        while i < 100:
            i += 1
            im = q.get()
            print("writing...")
            writer.write(im)
            if i >= 100:
                break

        print("Write utilisation equals {} fps.".format((time.time() - started_at) / 100))

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
