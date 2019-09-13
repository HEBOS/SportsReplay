#!/usr/bin/env python3
import os
import time
import cv2
import numpy as np
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
        self.frisbee_id = self.class_names.index(self.config.activity_detector["frisbee"])

        # load the object detection network
        started_at = time.time()
        detected_frames = 0

        classes = None
        with open(os.path.join(os.getcwd(), "networks", "class_labels.txt"), 'r') as f:
            classes = [line.strip() for line in f.readlines()]
        colors = np.random.uniform(0, 255, size=(len(classes), 3))

        net = cv2.dnn.readNetFromDarknet(os.path.join(os.getcwd(), "networks", "yolov3.cfg"),
                                         os.path.join(os.getcwd(), "networks", "yolov3.weights"))
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_VKCOM)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_VULKAN)
        layers = self.get_output_layers(net)

        d = 0
        for jpg_file in self.samples:
            d += 1
            print("Detecting in frame {}.".format(d))
            image = cv2.imread(jpg_file)

            width = image.shape[1]
            height = image.shape[0]
            scale = 1 / 255

            blob = cv2.dnn.blobFromImage(image, scale, (416, 416), (0, 0, 0), True, crop=False)

            net.setInput(blob)

            detect_start = time.time()
            outs = net.forward(layers)
            print("Detection took {} seconds.".format(time.time() - detect_start))

            class_ids = []
            confidences = []
            boxes = []
            conf_threshold = 0.5
            nms_threshold = 0.4

            for out in outs:
                for detection in out:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    if confidence > 0.5:
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        x = center_x - w / 2
                        y = center_y - h / 2
                        class_ids.append(class_id)
                        confidences.append(float(confidence))
                        boxes.append([x, y, w, h])

            indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

            for i in indices:
                i = i[0]
                box = boxes[i]
                x = box[0]
                y = box[1]
                w = box[2]
                h = box[3]
                self.draw_prediction(image,
                                     class_ids[i],
                                     confidences[i],
                                     round(x),
                                     round(y),
                                     round(x + w),
                                     round(y + h),
                                     colors,
                                     classes)

            if len(indices) > 0:
                detected_frames += 1

            cv2.imwrite(os.path.join("tmp", os.path.basename(jpg_file)), image)

        print("GPU utilisation equals {} fps.".format(int(len(self.samples) / (time.time() - started_at))))
        print("Detected objects: {}".format(balls_identified))
        print("Frames with the ball: {}/{}".format(detected_frames, len(self.samples)))

    def get_class_names(self) -> List[str]:
        labels = self.config.activity_detector["labels"]
        return open(labels).read().strip().split("\n")

    def get_output_layers(self, net):
        layer_names = net.getLayerNames()

        output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

        return output_layers

    def draw_prediction(self, img, class_id, confidence, x, y, x_plus_w, y_plus_h, colors, classes):
        label = str(classes[class_id])

        color = colors[class_id]

        cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)

        cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


if __name__ == "__main__":
    st = DetectorTest()
