import os
import queue
import threading
import concurrent.futures
import cv2
import imutils
import time
import multiprocessing as mp
from typing import List

from ActivityDetector.AiModelConfig import AiModelConfig
from Mask_RCNN.mmrcnn import model as modellib
from Shared.Configuration import Configuration
from Shared.LogHandler import LogHandler
from Shared.SharedFunctions import SharedFunctions


class SpeedTest(object):
    def __init__(self):

        self.sample_directory = os.path.normpath(r"{}/ActivityDetector/SampleImages".format(os.getcwd()))
        self.samples = [os.path.normpath(r"{}/{}".format(self.sample_directory, fi))
                        for fi in os.listdir(self.sample_directory)
                        if os.path.isfile(os.path.join(self.sample_directory, fi)) and fi.lower().endswith(".jpg")]

        self.config = Configuration().activity_detector
        self.class_names = self.get_class_names()
        self.sports_ball_id = self.class_names.index("sports ball")

        # Logger
        self.logger = LogHandler("detector")
        self.logger.info("Detector on has started detection.")

        started_at = time.time()
        self.detection_thread = None

        mp.set_start_method('spawn', force=True)
        self.start_detection()
        print("GPU utilisation equals {} fps.".format(100 / (time.time() - started_at)))

    def detect(self):
        model = self.init_ai_model()

        try:
            for b in range(0, 100):
                sample_name = self.samples[b]
                image: cv2.UMat = cv2.imread(sample_name, cv2.IMREAD_COLOR)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image = imutils.resize(image, width=512)

                result = model.detect([image], verbose=1)[0]

        except Exception as ex:
            print(ex)
            self.logger.error("Detector is in error state.")

    def start_detection(self):
        self.detection_thread = threading.Thread(target=self.detect, args=())
        self.detection_thread.start()
        self.detection_thread.join()

    def get_class_names(self) -> List[str]:
        labels = self.config["labels"]
        return open(labels).read().strip().split("\n")

    def init_ai_model(self) -> modellib.MaskRCNN:
        ai_model_config = AiModelConfig()

        model = modellib.MaskRCNN(mode="inference", config=ai_model_config, model_dir=os.getcwd())
        model.load_weights(self.config["weights"], by_name=True)

        return model


if __name__ == "__main__":
    st = SpeedTest()

