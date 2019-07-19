from ActivityDetector.AiModelConfig import AiModelConfig
from Mask_RCNN.mrcnn import model as modellib
from Shared.Configuration import Configuration
# from mrcnn import visualize
import numpy as np
import colorsys
import imutils
import cv2
import os
import datetime


class Detector(object):
    def __init__(self, ai_queues):
        self.ai_queues = ai_queues
        self.stop_detection = False

        config = Configuration().activity_detector
        self.output_directory = config["output-directory"]

        labels = config["labels"]
        self.class_names = open(labels).read().strip().split("\n")
        hsv = [(i / len(self.class_names), 1, 1.0) for i in range(len(self.class_names))]
        self.colors = list(map(lambda c: colorsys.hsv_to_rgb(*c), hsv))

        ai_model_config = AiModelConfig()
        self.model = modellib.MaskRCNN(mode="inference", config=ai_model_config,
                                  model_dir=os.getcwd())
        self.model.load_weights(config["weights"], by_name=True)

    def detect(self):
        first_frames_retrieved = 0
        queue_to_first_frame_is_retrieved = {}
        for index, queue in enumerate(self.ai_queues):
            queue_to_first_frame_is_retrieved[index] = False

        while not self.stop_detection:
            for index, queue in enumerate(self.ai_queues):
                try:
                    captured_frame = queue.get(block=False)

                    if queue_to_first_frame_is_retrieved[index] is False:
                        first_frames_retrieved += 1
                        queue_to_first_frame_is_retrieved[index] = True

                    image = captured_frame.frame
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    image = imutils.resize(image, width=512)
                except:
                    if first_frames_retrieved == len(self.ai_queues):
                        self.stop_detection = True
                        break
                    continue

                # perform a forward pass of the network to obtain the results
                print("[INFO] making predictions with Mask R-CNN...")
                r = self.model.detect([image], verbose=1)[0]

                # loop over of the detected object's bounding boxes and masks
                for i in range(0, r["rois"].shape[0]):
                    # extract the class ID and mask for the current detection, then
                    # grab the color to visualize the mask (in BGR format)
                    classID = r["class_ids"][i]
                    mask = r["masks"][:, :, i]
                    color = self.colors[classID][::-1]

                    # visualize the pixel-wise mask of the object
                    # image = visualize.apply_mask(image, mask, color, alpha=0.5)

                # convert the image back to BGR so we can use OpenCV's drawing
                # functions
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                identified_sports_ball = False

                # loop over the predicted scores and class labels
                for i in range(0, len(r["scores"])):
                    # extract the bounding box information, class ID, label, predicted
                    # probability, and visualization color
                    (startY, startX, endY, endX) = r["rois"][i]
                    classID = r["class_ids"][i]
                    label = self.class_names[classID]
                    if label == 'sports ball':
                        identified_sports_ball = True
                    score = r["scores"][i]
                    color = [int(c) for c in np.array(self.colors[classID]) * 255]

                    # draw the bounding box, class label, and score of the object
                    # cv2.rectangle(image, (startX, startY), (endX, endY), color, 2)
                    text = "{}: {:.3f}".format(label, score)
                    y = startY - 10 if startY - 10 > 10 else startY + 10
                    cv2.putText(image, text, (startX, y), cv2.FONT_HERSHEY_SIMPLEX,
                                0.6, color, 2)