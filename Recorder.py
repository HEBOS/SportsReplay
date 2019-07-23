#!/usr/bin/env pypy
import time
import multiprocessing as mp
import cv2
import os

from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions
from Recorder.VideoRecorder import VideoRecorder
from ActivityDetector.Detector import Detector


def start_single_camera(camera_number, address, path, fps, start_of_recording, scheduled_end_of_recording, config, ai_queue):
    building = config.common["building"]
    playground = config.common["playground"]

    if not os.path.isdir(path):
        os.mkdir(path)

    recording_path = SharedFunctions.get_recording_path(path, building, playground, start_of_recording)

    if not os.path.isdir(recording_path):
        os.mkdir(recording_path)

    video = VideoRecorder(camera_number,
                          address,
                          recording_path,
                          fps,
                          scheduled_end_of_recording,
                          playground,
                          ai_queue)
    video.record()


def start_activity_detection(ai_queues):
    Detector(ai_queues)


def run_main():
    config = Configuration()
    eor = time.time() + int(config.common["playtime"])
    sor = time.time()
    video_addresses = str(config.recorder["video"]).split(",")
    recording_path = os.path.normpath(r"{}".format(config.recorder["recording-path"]))

    if not os.path.isdir(recording_path):
        os.mkdir(recording_path)

    ai_queues = []
    processes = []
    i = 0
    for v in video_addresses:
        i += 1
        ai_queue = mp.Queue()
        ai_queues.append(ai_queue)

        video_path = v
        if ".mp4" in v:
            video_path = os.path.normpath(r"{}".format(v))

        processes.append(mp.Process(target=start_single_camera,
                                    args=(i,
                                          video_path,
                                          os.path.normpath(r"{}/{}".format(recording_path, i)),
                                          int(config.recorder["fps"]),
                                          sor,
                                          eor,
                                          config,
                                          ai_queue)))

    processes.append(mp.Process(target=start_activity_detection, args=(ai_queues,)))

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_main()
