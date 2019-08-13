#!/usr/bin/env python3
import threading
import concurrent.futures
import jetson.inference
import jetson.utils
import os
import time
import multiprocessing as mp
from typing import List
from Shared.LogHandler import LogHandler
from Shared.CapturedFrame import CapturedFrame
from Shared.Linq import Linq


class Detector(object):
    def __init__(self, playground: int, ai_queues: List[mp.Queue], class_id: int, network: str, threshold: float):
        self.playground = playground
        self.ai_queues = ai_queues
        self.class_id = class_id
        self.network = network
        self.threshold = threshold

        # Logger
        self.logger = LogHandler("detector")

    def detect(self):
        ai_tasks = []
        detecting = True

        # load the object detection network
        net = jetson.inference.detectNet(self.network,
                                         [],
                                         float(self.threshold))

        queues_terminated = 0
        total_queues = len(self.ai_queues)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            try:
                while queues_terminated < total_queues and detecting:
                    time.sleep(0.001)
                    for index, ai_queue in enumerate(self.ai_queues):
                        try:
                            captured_frame: CapturedFrame = ai_queue.get()

                            if captured_frame is not None:
                                if os.path.isfile(captured_frame.filePath):
                                    image, width, height = jetson.utils.loadImageRGBA(captured_frame.filePath)

                                    # Detect object, based on class id
                                    detections = net.Detect(image, width, height)
                                    output_json_array = []
                                    for detection in detections:
                                        '''
                                            These properties are available:
                                                Left
                                                Right
                                                Top
                                                Bottom
                                                Width
                                                Height
                                                Confidence
                                                Instance
                                        '''
                                        if detection.ClassID == self.class_id:
                                            output_json = {
                                                "x0": int(detection.Left),
                                                "y0": int(detection.Top),
                                                "x1": int(detection.Right),
                                                "y1": int(detection.Bottom),
                                                "score": int(detection.Confidence)
                                            }
                                            output_json_array.append(output_json)

                                    objects_identified = len(output_json_array)

                                    if objects_identified > 0:
                                        jetson.utils.cudaDeviceSynchronize()
                                        if objects_identified > 1:
                                            print("[!] More than one ball identified in frame!")
                                        captured_frame.json = output_json_array
                                        ai_task = executor.submit(captured_frame.save_json)
                                        ai_tasks.append(ai_task)
                                else:
                                    # If less than 20 seconds elapsed, requeue the frame, otherwise it is lost
                                    if time.time() - captured_frame.snapshot_time < 5:
                                        ai_queue.put(captured_frame, block=True, timeout=2)
                            else:
                                queues_terminated += 1
                                break
                        except Exception as ex:
                            if time.time() - captured_frame.snapshot_time < 5:
                                ai_queue.put(captured_frame, block=True, timeout=2)
                            else:
                                print("Unsuccessful in retrieving image from ai_queue")
                                detecting = False
            except:
                self.logger.error('Detector on playground {} is in error state.'.format(self.playground))

        concurrent.futures.wait(fs=ai_tasks, timeout=3, return_when="ALL_COMPLETED")
        net.Detection = None
        jetson.utils.cudaDeviceSynchronize()

