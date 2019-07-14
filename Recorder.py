#!/usr/bin/env pypy
import time
import multiprocessing as mp
import cv2
import os
import subprocess
import platform

from Shared.Configuration import Configuration
from Recorder.VideoRecorder import VideoRecorder


def start_single_camera(camera_number, address, path, fps, scheduled_end_of_recording, config):
    client = int(config.common["client"])
    playground = config.common["playground"]

    if not os.path.isdir(path):
        os.mkdir(path)

    video = VideoRecorder(camera_number,
                          address,
                          path,
                          fps,
                          scheduled_end_of_recording,
                          client,
                          playground)
    video.record()


def run_main():
    config = Configuration()
    eor = time.time() + int(config.common["playtime"])
    video_addresses = str(config.recorder["video"]).split(",")
    recording_path = os.path.normpath(r"{}".format(config.recorder["recording-path"]))

    if not os.path.isdir(recording_path):
        os.mkdir(recording_path)

    processes = []
    i = 0
    for v in video_addresses:
        i += 1
        processes.append(mp.Process(target=start_single_camera,
                                    args=(i,
                                          v,
                                          os.path.normpath(r"{}/{}".format(recording_path, i)),
                                          int(config.recorder["fps"]),
                                          eor,
                                          config)))

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_main()
