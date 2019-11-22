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

        input_pipeline = "rtspsrc location={location} latency={latency} " \
                         "user-id={user} user-pw={password} " \
                         "! queue " \
                         "! rtph264depay " \
                         "! h264parse " \
                         "! omxh264dec " \
                         "! videorate max-rate={fps} drop-only=true average-period=5000000 " \
                         "! video/x-raw,framerate={fps}/1 " \
                         "! nvvidconv " \
                         "! video/x-raw(memory:NVMM),format=BGRx " \
                         "! queue " \
                         "! nvvidconv " \
                         "! video/x-raw,format=BGRx" \
                         "! videoconvert " \
                         "! video/x-raw,format=BGR " \
                         "! appsink sync=true".format(location=video_addresses[0],
                                                   fps=fps,
                                                   width=width,
                                                   height=height,
                                                   user="sportsreplay",
                                                   password="Spswd001.",
                                                   latency=2000)

        output_pipeline = "appsrc " \
                          "! capsfilter caps='video/x-raw,format=I420,framerate={fps}/1' " \
                          "! videoconvert " \
                          "! capsfilter caps='video/x-raw,format=BGRx,interpolation-method=1' " \
                          "! nvvideoconvert " \
                          "! capsfilter caps='video/x-raw(memory:NVMM)' " \
                          "! nvv4l2h264enc maxperf-enable=true " \
                          "! h264parse " \
                          "! qtmux " \
                          "! filesink location={video}".format(video="output.mp4v",
                                                               fps=fps,
                                                               width=width,
                                                               height=height)

        print("VideoCapture:")
        print("-----------------------------------------------------------------------------------------------")
        print(input_pipeline)
        capture = cv2.VideoCapture(input_pipeline, cv2.CAP_GSTREAMER)

        print("Capture opened={}".format(capture.isOpened()))
        print('Codec FOURCC: {}'.format(hex(int(capture.get(6)))))
        print('Codec pixel FOURCC: {}'.format(hex(int(capture.get(46)))))

        success, image = capture.read()
        print("Image shape: ", image.shape)

        q = queue.Queue(maxsize=10000)
        started_at = time.time()
        j = 0
        while time.time() - started_at <= 2:
            grabbed, img = capture.read()
            if grabbed:
                j += 1
                #if j % 10 == 0:
                #    cv2.imwrite("out.jpg", img)
                try:
                    print("Grabbed {}".format(j))
                    q.put(img)
                except:
                    break

        print("Read utilisation equals {} fps.".format(j / (time.time() - started_at)))
        print("")
        print("")
        print("VideoWriter:")
        print(output_pipeline)
        print("-----------------------------------------------------------------------------------------------")
        # cv2.VideoWriter_fourcc(*'H265'),

        writer = cv2.VideoWriter(output_pipeline, cv2.VideoWriter_fourcc(*'mp4v'),
                                 fps, (width, height), True)

        started_at = time.time()
        i = 0
        while i <= fps * 10:
            i += 1
            if q.qsize() == 0:
                break
            im = q.get()
            print("Writing {}".format(i))
            writer.write(im)

        print("Write utilisation equals {} fps.".format((fps * 10) / (time.time() - started_at)))

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
