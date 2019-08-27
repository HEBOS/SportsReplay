#!/usr/bin/env python3
import jetson.inference
import jetson.utils
import os
import time
import cv2
from typing import List

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
        net = jetson.inference.detectNet(self.config.activity_detector["network"],
                                         [],
                                         float(self.config.activity_detector["threshold"]))

        started_at = time.time()
        detected_frames = 0
        #size = (960, 544)
        size = (480, 272)
        for jpg_file in self.samples:
            img = cv2.cvtColor(cv2.resize(cv2.imread(jpg_file), size), cv2.COLOR_RGB2RGBA)
            cuda_image = jetson.utils.cudaFromNumpy(img)
            detections = net.Detect(cuda_image, size[0], size[1])
            if len(detections) > 0:
                detected_frame = False
                for detection in detections:
                    if detection.ClassID == self.sports_ball_id:
                        balls_identified += 1
                        detected_frame = True
                jetson.utils.cudaDeviceSynchronize()

                if detected_frame:
                    detected_frames += 1

        print("GPU utilisation equals {} fps.".format(int(len(self.samples) / (time.time() - started_at))))
        print("Detected objects: {}".format(balls_identified))
        print("Frames with the ball: {}/{}".format(detected_frames, len(self.samples)))

    def get_class_names(self) -> List[str]:
        labels = self.config.activity_detector["labels"]
        return open(labels).read().strip().split("\n")


if __name__ == "__main__":
    st = DetectorTest()
