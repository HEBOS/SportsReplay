#!/usr/bin/env python3
import time
import multiprocessing as mp
import os
import signal
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
                    client, building, playground, target_path, start_of_capture, end_of_capture,
                    frames_to_skip)

    video = VideoRecorder(camera, ai_queue)
    video.start()


def start_activity_detection(playground: int, ai_queues: List[mp.Queue], class_id: int, network: str, threshold: float):
    detector = Detector(playground, ai_queues, class_id, network, threshold)
    detector.detect()


def run_main():
    config = Configuration()

    # Schedule the start and end of capture 3 seconds ahead, so that all camera start at the same time
    playtime = int(config.common["playtime"])
    start_of_capture = time.time() + 10
    end_of_capture = start_of_capture + playtime
    video_addresses = str(config.recorder["video"]).split(",")

    # Ensure that root directory exists
    dump_path = os.path.normpath(r"{}".format(config.common["dump-path"]))
    SharedFunctions.ensure_directory_exists(dump_path)

    # Ensure that recording directory exists
    recording_path = os.path.join(dump_path, config.recorder["recording-path"])
    SharedFunctions.ensure_directory_exists(recording_path)

    # Ensure that post recording directory exists
    post_recording_path = os.path.join(dump_path, config.post_recorder["post-recording-path"])
    SharedFunctions.ensure_directory_exists(post_recording_path)

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
    width = int(config.recorder["width"])
    height = int(config.recorder["height"])
    class_id = SharedFunctions.get_class_id(os.path.join(os.getcwd(), config.activity_detector["labels"]),
                                            config.activity_detector["sports-ball"])
    network = config.activity_detector["network"]
    threshold = config.activity_detector["threshold"]

    # Ensure session directory exists
    session_path = SharedFunctions.get_recording_path(recording_path, building, playground, start_of_capture)
    SharedFunctions.ensure_directory_exists(session_path)

    for v in video_addresses:
        i += 1
        ai_queue = mp.Queue()
        ai_queues.append(ai_queue)

        # Ensure video_delays array is initialised
        if len(frames_to_skip) != i:
            frames_to_skip.append("0")

        source_path = v

        # If video source is not camera, but mp4 file, fix the path
        if ".mp4" in v:
            source_path = os.path.normpath(r"{}".format(v))

        # Ensure directory for particular camera exists
        camera_path = os.path.normpath(r"{}/{}".format(session_path, i))
        SharedFunctions.ensure_directory_exists(camera_path)

        processes.append(mp.Process(target=start_single_camera,
                                    args=(i,
                                          source_path,
                                          fps,
                                          width,
                                          height,
                                          client,
                                          building,
                                          playground,
                                          camera_path,
                                          start_of_capture,
                                          end_of_capture,
                                          int(frames_to_skip[i - 1]),
                                          ai_queue
                                          )))

    processes.append(mp.Process(target=start_activity_detection,
                                args=(playground, ai_queues, class_id, network, threshold)))

    started_at = time.time()
    for p in processes:
        p.start()

    try:
        for p in processes:
            p.join()

        # Moving files to a new location
        print("Moving files to post processing directory...")
        new_path = session_path.replace(recording_path, post_recording_path)
        os.rename(session_path, new_path)

        # Allow VideoMaker to take over
        SharedFunctions.create_text_file(os.path.normpath(r"{}/READY.TXT").format(new_path),
                                         "Recoding finished")
        print("Done")
    except:
        # Remove the whole session directory
        print("Directory {} has been removed, due to errors.".format(session_path))
        # shutil.rmtree(session_path)
    finally:
        print("Recording session finished after {} seconds.".format(time.time() - started_at))


if __name__ == "__main__":
    run_main()
