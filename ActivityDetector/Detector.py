#!/usr/bin/env python3
import queue
import threading
import concurrent.futures
import multiprocessing as mp
import jetson.inference
import jetson.utils

from Shared.Configuration import Configuration
from Shared.LogHandler import LogHandler
from Shared.Camera import Camera


class Detector(object):
    def __init__(self, playground: int, ai_queues: list, width: int, height: int, class_id: int,
                 network: str, threshold: float):
        self.playground = playground
        self.ai_queues = ai_queues
        self.class_id = class_id
        self.network = network
        self.threshold = threshold
        self.width = width
        self.height = height

        self.output_queue = queue.Queue(maxsize=10000)
        self.stop_detection = False
        self.output_threads = []

        self.config = Configuration().activity_detector

        # Logger
        self.logger = LogHandler("detector")
        self.logger.info('Detector on playground {} has ras started detection.'.format(playground))

        self.detection_thread = None

        mp.set_start_method('spawn', force=True)
        self.start_detection()

    def detect(self):
        queue_index_to_is_first_frame_retrieved = {}
        queue_index_to_is_queue_empty = {}
        for index, ai_queue in enumerate(self.ai_queues):
            queue_index_to_is_first_frame_retrieved[index] = False
            queue_index_to_is_queue_empty[index] = True

        number_of_queues = len(self.ai_queues)
        first_frames_retrieved = 0
        queues_currently_empty = number_of_queues
        ai_tasks = []

        # load the object detection network
        net = jetson.inference.detectNet(self.config.activity_detector["network"],
                                         [],
                                         float(self.config.activity_detector["threshold"]))

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            try:
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
                        except Exception as ex:
                            print("Unsuccessful in retrieving image from ai_queue: " + str(ex))
                            if ai_queue.empty():
                                queue_index_to_is_queue_empty[index] = True
                                queues_currently_empty += 1

                                if first_frames_retrieved == number_of_queues and \
                                        queues_currently_empty == number_of_queues:
                                    print("All queues are empty! Stopping detection.")
                                    self.stop_detection = True
                                    break
                            continue

                        '''
                            These properties are available
                            Left, Right, Top, Bottom
                            Width, Height
                            Confidence, Instance
                        '''
                        detections = net.Detect(image, self.width, self.height)
                        output_json_array = []
                        for detection in detections:
                            if detection.ClassID == self.class_id:
                                output_json = {
                                    "x0": int(detection.Left),
                                    "y0": int(detection.Top),
                                    "x1": int(detection.Right),
                                    "y1": int(detection.Bottom),
                                    "score": int(detection.Confidence)
                                }
                                output_json_array.append(output_json)

                        balls_identified = len(output_json_array)

                        if balls_identified > 0:
                            if balls_identified > 1:
                                print("[!] More than one ball identified in frame!")
                            captured_frame.json = output_json_array
                            ai_task = executor.submit(captured_frame.save_json)
                            ai_tasks.append(ai_task)
            except:
                self.stop_detection = True
                self.logger.error('Detector on playground {} is in error state.'.format(self.playground))
            finally:
                concurrent.futures.wait(fs=ai_tasks, timeout=10, return_when="ALL_COMPLETED")

    def start_detection(self):
        self.detection_thread = threading.Thread(target=self.detect, args=())
        self.detection_thread.start()
        self.detection_thread.join()

    def stop(self):
        self.stop_detection = True
