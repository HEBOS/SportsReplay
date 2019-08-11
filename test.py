#!/usr/bin/env python3
import tensorflow as tf
import cv2
import os
import time

# The TensorRT inference graph file downloaded from Colab or your local machine.
model_path = os.path.join(os.getcwd(), "ActivityDetector")

input_names = ['image_tensor']

# Create session and load graph
tf_config = tf.ConfigProto()
tf_config.gpu_options.allow_growth = True

with tf.Session(graph=tf.Graph(), config=tf_config) as tf_sess:
    tf.saved_model.loader.load(tf_sess, [tf.saved_model.tag_constants.SERVING], model_path)

    tf_input = tf_sess.graph.get_tensor_by_name(input_names[0] + ':0')
    tf_scores = tf_sess.graph.get_tensor_by_name('detection_scores:0')
    tf_boxes = tf_sess.graph.get_tensor_by_name('detection_boxes:0')
    tf_classes = tf_sess.graph.get_tensor_by_name('detection_classes:0')
    tf_num_detections = tf_sess.graph.get_tensor_by_name('num_detections:0')

    images = os.listdir(os.path.join(os.getcwd(), "ActivityDetector",  "SampleImages"))
    absolute_paths = [os.path.join("ActivityDetector", "SampleImages", image) for image in images]

    balls_identified = 0
    start_time = time.time()
    for image_path in absolute_paths:
        image = cv2.imread(image_path)
        image = cv2.resize(image, (300, 300))

        scores, boxes, classes, num_detections = tf_sess.run([tf_scores,
                                                              tf_boxes,
                                                              tf_classes,
                                                              tf_num_detections],
                                                             feed_dict={tf_input: image[None, ...]})
        boxes = boxes[0]  # index by 0 to remove batch dimension
        scores = scores[0]
        classes = classes[0]
        num_detections = int(num_detections[0])

        if 37 in classes:
            print("identified ball")
            balls_identified += 1

    end_time = time.time()

    fps = len(images) / (end_time - start_time)
    print("fps: " + str(fps))
    print("identified " + str(balls_identified) + " out of " + str(len(images)) + " frames")