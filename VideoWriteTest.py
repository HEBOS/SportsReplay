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

        sample_directory = os.path.normpath(r"{}/ActivityDetector/SampleImages".format(os.getcwd()))
        samples = [os.path.normpath(r"{}/{}".format(sample_directory, fi))
                   for fi in os.listdir(sample_directory)
                   if os.path.isfile(os.path.join(sample_directory, fi)) and fi.lower().endswith(".jpg")]

        # Ensure that root directory exists
        dump_path = os.path.normpath(r"{}".format(config.common["dump-path"]))
        SharedFunctions.ensure_directory_exists(dump_path)

        # Ensure that video making directory exists
        video_making_path = os.path.join(dump_path, config.video_maker["video-making-path"])
        SharedFunctions.ensure_directory_exists(video_making_path)

        fps = int(config.recorder["fps"])
        width = int(config.recorder["width"])
        height = int(config.recorder["height"])
        output_video_file = os.path.join(video_making_path, SharedFunctions.get_output_video(video_making_path,
                                                                                             1,
                                                                                             1,
                                                                                             time.time()))
        output_pipeline = "appsrc " \
                          "! autovideoconvert " \
                          "! video/x-raw,format=(string)I420,width={width},height={height},framerate={fps}/1 " \
                          "! omxh264enc ! video/x-h264,stream-format=(string)byte-stream " \
                          "! h264parse " \
                          "! qtmux " \
                          "! filesink location={video}.avi".format(width=width,
                                                                   height=height,
                                                                   fps=fps,
                                                                   video=output_video_file)

        print(output_pipeline)
        out = cv2.VideoWriter(output_pipeline, cv2.VideoWriter_fourcc(*'X264'), fps, (width, height))
        started_at = time.time()
        rendered_images = 0
        for r in range(0, 100):
            for im in samples:
                sample_image = cv2.imread(im)
                out.write(sample_image)

                del sample_image
                if rendered_images % fps == 0:
                    gc.collect()
                    print("Rendered {} second".format(int(rendered_images / fps) + 1))

                rendered_images += 1
                if rendered_images == 749:
                    break
            if rendered_images == 749:
                break

        print("For 30 secs of video, at {} fps, it took {} secs to complete.".format(fps, time.time() - started_at))
        out.release()
        self.clear_cv_from_memory()
        gc.collect()

    def clear_cv_from_memory(self):
        cv2.waitKey(1)
        cv2.destroyAllWindows()
        for i in range(1, 5):
            cv2.waitKey(1)


if __name__ == "__main__":
    st = VideoWriteTest()
