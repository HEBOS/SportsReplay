#!/usr/bin/env python3
import os
import time
import cv2
from typing import List
from Darknet import DarknetDetector

from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions


class DetectorTest(object):
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
        net = DarknetDetector.DarknetDetector(
            os.path.join(os.getcwd(), self.config.activity_detector["network-config"]),
            os.path.join(os.getcwd(), self.config.activity_detector["network-weights"]),
            os.path.join(os.getcwd(), self.config.activity_detector["coco-config"]),
            (480, 270))

        started_at = time.time()
        detected_frames = 0
        for jpg_file in self.samples[:20]:
            img = cv2.imread(jpg_file)
            detections = net.detect(img, True)
            if detections is not None:
                if len(detections) > 0:
                    detected_frame = False
                    for detection in detections:
                        if detection.ClassID == self.sports_ball_id:
                            balls_identified += 1
                            detected_frame = True

                    if detected_frame:
                        detected_frames += 1

        print("GPU utilisation equals {} fps.".format(int(20 / (time.time() - started_at))))
        print("Detected objects: {}".format(balls_identified))
        print("Frames with the ball: {}/{}".format(detected_frames, 20))

    def get_class_names(self) -> List[str]:
        labels = self.config.activity_detector["coco-labels"]
        return open(labels).read().strip().split("\n")


if __name__ == "__main__":
    st = DetectorTest()
