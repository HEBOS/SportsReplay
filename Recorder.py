#!/usr/bin/env pypy
import time
import multiprocessing as mp
import cv2
import os
import shutil
from typing import List

from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions
from Recorder.VideoRecorder import VideoRecorder
from ActivityDetector.Detector import Detector
from Shared.Camera import Camera


def start_single_camera(camera_id: int, source: str, fps: int, width: int, height: int, client: int,
                        building: int, playground: int, target_path: str,
                        start_of_capture: time, end_of_capture: time, frames_to_skip: int, ai_queue: mp.Queue):

    camera = Camera(camera_id, source, fps, width, height,
                    client, building, playground, target_path, start_of_capture, end_of_capture, frames_to_skip)

    video = VideoRecorder(camera, ai_queue)
    video.start()


def start_activity_detection(playground: int, ai_queues: list):
    Detector(playground, ai_queues)
    pass


def run_main():
    config = Configuration()

    # Schedule the start and end of capture 3 seconds ahead, so that all camera start at the same time
    start_of_capture = time.time() + 10
    end_of_capture = start_of_capture + int(config.common["playtime"])

    video_addresses = str(config.recorder["video"]).split(",")

    # Ensure that root recording directory exists
    root_recording_path = os.path.normpath(r"{}".format(config.recorder["recording-path"]))
    SharedFunctions.ensure_directory_exists(root_recording_path)

    # Ensure that root post recording directory exists
    root_post_recording_path = os.path.normpath(r"{}".format(config.post_recorder["post-recording-path"]))
    SharedFunctions.ensure_directory_exists(root_post_recording_path)

    # This is for the testing purposes only, and required when video source are the files, not cameras
    frames_to_skip = str(config.recorder["frames-to-skip"]).split(",")

    ai_queues = []
    processes = []
    i = 0

    # Get main configuration settings
    client = int(config.common["client"])
    building = int(config.common["building"])
    playground = int(config.common["playground"])
    fps = int(config.recorder["fps"])

    # Ensure session directory exists
    session_path = SharedFunctions.get_recording_path(root_recording_path, building, playground, start_of_capture)
    SharedFunctions.ensure_directory_exists(session_path)

    for v in video_addresses:
        i += 1
        ai_queue = mp.Queue()
        ai_queues.append(ai_queue)

        # If video source is not camera, but mp4 file, fix the path
        source_path = v
        if ".mp4" in v:
            source_path = os.path.normpath(r"{}".format(v))

        # Ensure video_delays array is initialised
        if len(frames_to_skip) != i:
            frames_to_skip.append("0")

        # Ensure directory for particular camera exists
        camera_path = os.path.normpath(r"{}/{}".format(session_path, i))
        SharedFunctions.ensure_directory_exists(camera_path)

        # OVDJE DODATI STREAM-ANJE SA MP4 FILE-A PUTEM FFMPEG-A

        processes.append(mp.Process(target=start_single_camera,
                                    args=(i,
                                          source_path,
                                          fps,
                                          1280,
                                          720,
                                          client,
                                          building,
                                          playground,
                                          camera_path,
                                          start_of_capture,
                                          end_of_capture,
                                          float(frames_to_skip[i-1]),
                                          ai_queue)))

    processes.append(mp.Process(target=start_activity_detection, args=(playground, ai_queues)))

    started_at = time.time()
    for p in processes:
        p.start()

    try:
        for p in processes:
            p.join()

        # Moving files to a new location
        print("Moving files to post processing directory...")
        new_path = session_path.replace(root_recording_path, root_post_recording_path)
        os.rename(session_path, new_path)
        # Allow VideoMaker to take over
        SharedFunctions.create_text_file(os.path.normpath(r"{}/READY.TXT").format(new_path),
                                         "Recoding finished")
        print("Done")
    except:
        # Remove the whole session directory
        print("Directory {} has been removed, due to errors.".format(session_path))
        shutil.rmtree(session_path)
    finally:
        cv2.destroyAllWindows()
        print("Recording session finished after {} seconds.".format(time.time() - started_at))


if __name__ == "__main__":
    run_main()
