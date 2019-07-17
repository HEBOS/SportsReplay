

# USAGE
# python maskrcnn_predict.py --weights mask_rcnn_coco.h5 --labels coco_labels.txt --image images/30th_birthday.jpg

# import the necessary packages
from ActivityDetector.MLModelConfig import MLModelConfig
from Mask_RCNN.mrcnn import model as modellib
from Shared.Configuration import Configuration
# from mrcnn import visualize
import numpy as np
import colorsys
import argparse
import imutils
# import random
import cv2
import os
import datetime
from pathlib import Path


class Detector(object):
    def __init__(self, recording_path, camera_count):
        self.camera_number_to_image_filenames_list = self.get_image_filenames_for_each_camera(recording_path, camera_count)

    def get_image_filenames_for_each_camera(self, recording_path, camera_count):
        camera_number_to_image_filenames_list = {}
        for i in range(1, camera_count + 1):
            camera_images_path = os.path.normpath(r"{}/{}".format(recording_path, i))
            frame_filenames = [filename for filename in Path(camera_images_path).glob('*.png')]
            camera_number_to_image_filenames_list[i] = frame_filenames
            return camera_number_to_image_filenames_list


labels = "/home/luka/PycharmProjects/r-cnn-gpu/keras-mask-rcnn/coco_labels.txt"
weights = "/home/luka/PycharmProjects/r-cnn-gpu/keras-mask-rcnn/mask_rcnn_coco.h5"
directory = "/home/luka/PycharmProjects/r-cnn-gpu/keras-mask-rcnn/images/input/"

# load the class label names from disk, one label per line
CLASS_NAMES = open(labels).read().strip().split("\n")

# generate random (but visually distinct) colors for each class label
# (thanks to Matterport Mask R-CNN for the method!)
hsv = [(i / len(CLASS_NAMES), 1, 1.0) for i in range(len(CLASS_NAMES))]
COLORS = list(map(lambda c: colorsys.hsv_to_rgb(*c), hsv))

# initialize the inference configuration
config = MLModelConfig()

# initialize the Mask R-CNN model for inference and then load the
# weights
print("[INFO] loading Mask R-CNN model...")

model = modellib.MaskRCNN(mode="inference", config=config,
    model_dir=os.getcwd())
model.load_weights(weights, by_name=True)


directory_with_images = directory
image_filenames = os.listdir(directory_with_images)
loop_iteration = 0
sports_ball_identifications_count = 0
start_time = None

for image_filename in image_filenames:
    if loop_iteration == 1:
        start_time = str(datetime.datetime.now())

    abs_path_of_image_file = directory_with_images + image_filename

    try:
        image = cv2.imread(abs_path_of_image_file)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = imutils.resize(image, width=512)
    except:
        continue

    # perform a forward pass of the network to obtain the results
    print("[INFO] making predictions with Mask R-CNN...")
    r = model.detect([image], verbose=1)[0]

    # loop over of the detected object's bounding boxes and masks
    # for i in range(0, r["rois"].shape[0]):
        # extract the class ID and mask for the current detection, then
        # grab the color to visualize the mask (in BGR format)
        # classID = r["class_ids"][i]
        # mask = r["masks"][:, :, i]
        # color = COLORS[classID][::-1]

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
        label = CLASS_NAMES[classID]
        if label == 'sports ball':
            identified_sports_ball = True
        score = r["scores"][i]
        color = [int(c) for c in np.array(COLORS[classID]) * 255]

        # draw the bounding box, class label, and score of the object
        # cv2.rectangle(image, (startX, startY), (endX, endY), color, 2)
        text = "{}: {:.3f}".format(label, score)
        y = startY - 10 if startY - 10 > 10 else startY + 10
        cv2.putText(image, text, (startX, y), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, color, 2)

        if identified_sports_ball:
            sports_ball_identifications_count += 1

    loop_iteration += 1
    # cv2.imshow("Output", image)
    # cv2.waitKey()

print("start time: " + start_time)
print("end time: " + str(datetime.datetime.now()))
print("total frames processed: " + str(loop_iteration))
print("number of frames with sports ball identified: " + str(sports_ball_identifications_count))