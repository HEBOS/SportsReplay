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

        output_video_path = os.path.join(dump_path, "video-test.mp4")
        out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

        started_at = time.time()

        rendered_images = 0

        for r in range(0, 100):
            for im in samples:
                sample_image = cv2.imread(im)
                out.write(sample_image)

                del sample_image
                if rendered_images % fps == 0:
                    gc.collect()
                    print("Rendered {} second".format(int((rendered_images + 1) / fps)))

                rendered_images += 1
                if rendered_images == 649:
                    break
            if rendered_images == 649:
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
