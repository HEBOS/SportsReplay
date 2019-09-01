#!/usr/bin/env python3
import jetson.inference
import jetson.utils
import os
import time
import cv2
from typing import List

from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions


class PointDetectorTest(object):
    def __init__(self):
        self.config = Configuration()
        self.class_names = self.get_class_names()
        self.sports_ball_id = self.class_names.index(self.config.activity_detector["sports-ball"])

        # load the object detection network
        net = jetson.inference.detectNet(self.config.activity_detector["network"],
                                         [],
                                         float(self.config.activity_detector["threshold"]))

        size = (480, 272)
        jpg_file = os.path.normpath(r"/home/sportsreplay/tmp/point-1.jpg")
        img = cv2.cvtColor(cv2.resize(cv2.imread(jpg_file), size), cv2.COLOR_RGB2RGBA)
        cuda_image = jetson.utils.cudaFromNumpy(img)
        detections = net.Detect(cuda_image, size[0], size[1])
        balls_identified = 0

        if len(detections) > 0:
            for detection in detections:
                if detection.ClassID == self.sports_ball_id:
                    print("Detected objects: left: {}, right: {}, top: {}, bottom: {}, width: {}, height: {}".format(
                        detection.Left,
                        detection.Right,
                        detection.Top,
                        detection.Bottom,
                        detection.Width,
                        detection.Height))

            jetson.utils.cudaDeviceSynchronize()

    def get_class_names(self) -> List[str]:
        labels = self.config.activity_detector["labels"]
        return open(labels).read().strip().split("\n")


if __name__ == "__main__":
    st = PointDetectorTest()
