#!/usr/bin/env python3
import jetson.inference
import jetson.utils
import os
import time
import cv2
from typing import List

from Shared.Configuration import Configuration


class SpeedTest(object):
    def __init__(self):
        balls_identified = 0
        self.sample_directory = os.path.normpath(r"{}/ActivityDetector/SampleImages".format(os.getcwd()))
        self.samples = [os.path.normpath(r"{}/{}".format(self.sample_directory, fi))
                        for fi in os.listdir(self.sample_directory)
                        if os.path.isfile(os.path.join(self.sample_directory, fi)) and fi.lower().endswith(".jpg")]

        self.config = Configuration()
        self.class_names = self.get_class_names()
        self.sports_ball_id = self.class_names.index(self.config.activity_detector["sports-ball"])

        # load the object detection network
        net = jetson.inference.detectNet(self.config.activity_detector["network"],
                                         [],
                                         float(self.config.activity_detector["threshold"]))

        started_at = time.time()

        for jpg_file in self.samples:
            img, width, height = jetson.utils.loadImageRGBA(jpg_file, zeroCopy=1)
            detections = net.Detect(img, width, height)
            for detection in detections:
                if detection.ClassID == self.sports_ball_id:
                    balls_identified += 1

        print("GPU utilisation equals {} fps.".format(int(len(self.samples) / (time.time() - started_at))))
        print("Detected objects: {}".format(balls_identified))

    def get_class_names(self) -> List[str]:
        labels = self.config.activity_detector["labels"]
        return open(labels).read().strip().split("\n")


if __name__ == "__main__":
    st = SpeedTest()
