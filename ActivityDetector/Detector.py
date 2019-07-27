import os
import queue
import threading

import cv2
import imutils
import time

from ActivityDetector.AiModelConfig import AiModelConfig
from Mask_RCNN.mrcnn import model as modellib
from Shared.Configuration import Configuration


class Detector(object):
    def __init__(self, ai_queues):
        self.ai_queues = ai_queues
        self.output_queue = queue.Queue(maxsize=10000)
        self.stop_detection = False
        self.output_threads = []

        self.config = Configuration().activity_detector
        self.output_directory = self.get_output_directory()
        self.class_names = self.get_class_names()
        self.sports_ball_id = self.class_names.index("sports ball")

        self.start_detection()

    def detect(self):
        model = self.init_ai_model()
        queue_index_to_is_first_frame_retrieved = {}
        queue_index_to_is_queue_empty = {}
        for index, ai_queue in enumerate(self.ai_queues):
            queue_index_to_is_first_frame_retrieved[index] = False
            queue_index_to_is_queue_empty[index] = True

        number_of_queues = len(self.ai_queues)
        first_frames_retrieved = 0
        queues_currently_empty = number_of_queues

        while not self.stop_detection:
            for index, ai_queue in enumerate(self.ai_queues):
                try:
                    captured_frame = ai_queue.get(block=False)
                    # poison pill found; aborting detection
                    if captured_frame is None:
                        self.stop_detection = True
                        break

                    if queue_index_to_is_first_frame_retrieved[index] is False:
                        first_frames_retrieved += 1
                        queue_index_to_is_first_frame_retrieved[index] = True
                    if queue_index_to_is_queue_empty[index] is True:
                        queue_index_to_is_queue_empty[index] = False
                        queues_currently_empty -= 1

                    image = captured_frame.frame
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    image = imutils.resize(image, width=512)

                except Exception as ex:
                    print("Unsuccessful in retrieving image from ai_queue: " + str(ex))
                    if ai_queue.empty():
                        queue_index_to_is_queue_empty[index] = True
                        queues_currently_empty += 1

                        if first_frames_retrieved == number_of_queues and queues_currently_empty == number_of_queues:
                            print("All queues are empty! Stopping detection.")
                            self.stop_detection = True
                            break
                    continue

                result = model.detect([image], verbose=1)[0]

                output_json_array = []

                for i in range(0, len(result["scores"])):
                    # extract the bounding box information, class ID and predicted probability
                    class_id = result["class_ids"][i]
                    if class_id == self.sports_ball_id:
                        (startY, startX, endY, endX) = result["rois"][i]
                        score = result["scores"][i]

                        output_json = {
                            "x0": int(startX),
                            "y0": int(startY),
                            "x1": int(endX),
                            "y1": int(endY),
                            "score": int(score)
                        }

                        output_json_array.append(output_json)

                if len(output_json_array) > 1:
                    print("[!] More than one ball identified in frame!")

                captured_frame.json = output_json_array
                captured_frame.json_directory = self.output_directory
                self.output_threads.append(captured_frame.save_json_async())

        for thread in self.output_threads:
            thread.join()

    def start_detection(self):
        detection_thread = threading.Thread(target=self.detect, args=())
        detection_thread.start()
        detection_thread.join()

    def stop(self):
        self.stop_detection = True
        self.detection_thread.join()

    def get_output_directory(self):
        output_directory = os.path.normpath(r"{}".format(self.config["output-directory"]))
        if not os.path.isdir(output_directory):
            os.mkdir(output_directory)
        return output_directory

    def get_class_names(self):
        labels = self.config["labels"]
        return open(labels).read().strip().split("\n")

    def init_ai_model(self):
        ai_model_config = AiModelConfig()

        model = modellib.MaskRCNN(mode="inference", config=ai_model_config, model_dir=os.getcwd())
        model.load_weights(self.config["weights"], by_name=True)

        return model
