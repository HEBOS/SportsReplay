#!/usr/bin/env python3
import time
import multiprocessing as mp
import os
import shutil
from typing import List
from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions
from Recorder.VideoRecorder import VideoRecorder
from ActivityDetector.Detector import Detector
from Shared.Camera import Camera
from VideoMaker.VideoMaker import VideoMaker


def start_single_camera(camera_id: int, source: str, fps: int, cdfps: float, width: int, height: int, client: int,
                        building: int, playground: int, target_path: str,
                        start_of_capture: time, end_of_capture: time, frames_to_skip: int, ai_queue: mp.Queue):

    camera = Camera(camera_id, source, fps, cdfps, width, height,
                    client, building, playground, target_path, start_of_capture, end_of_capture,
                    frames_to_skip)

    video = VideoRecorder(camera, ai_queue)
    video.start()


def start_activity_detection(playground: int, ai_queues: List[mp.Queue], class_id: int, network: str, threshold: float,
                             video_queue):
    detector = Detector(playground, ai_queues, class_id, network, threshold, video_queue)
    detector.detect()


def start_video_making(playground: int, video_queue: mp.Queue, output_video: str, width: int, height: int, fps: int):
    video_maker = VideoMaker(playground, video_queue, output_video, width, height, fps)
    video_maker.start()


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

    # Ensure that video making directory exists
    video_making_path = os.path.join(dump_path, config.video_maker["video-making-path"])
    SharedFunctions.ensure_directory_exists(video_making_path)

    # Ensure that streaming directory exists
    streaming_path = os.path.join(dump_path, config.video_maker["streaming-path"])
    SharedFunctions.ensure_directory_exists(streaming_path)

    # This is for the testing purposes only, and required when video source are the files, not cameras
    frames_to_skip = str(config.recorder["frames-to-skip"]).split(",")

    ai_queues = []
    video_queue = mp.Queue()
    processes = []
    i = 0

    # Get main configuration settings
    client = int(config.common["client"])
    building = int(config.common["building"])
    playground = int(config.common["playground"])
    fps = int(config.recorder["fps"])
    cdfps = float(config.activity_detector["cdfps"])
    width = int(config.recorder["width"])
    height = int(config.recorder["height"])
    class_id = SharedFunctions.get_class_id(os.path.join(os.getcwd(), config.activity_detector["labels"]),
                                            config.activity_detector["sports-ball"])
    network = config.activity_detector["network"]
    threshold = config.activity_detector["threshold"]

    # Ensure session directory exists
    session_path = SharedFunctions.get_recording_path(recording_path, building, playground, start_of_capture)
    SharedFunctions.ensure_directory_exists(session_path)

    output_video = SharedFunctions.get_output_video(video_making_path, building, playground, start_of_capture)

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
                                          cdfps,
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
                                args=(playground, ai_queues, class_id, network, threshold, video_queue)))

    processes.append(mp.Process(target=start_video_making,
                                args=(playground, video_queue, output_video, width, height, fps)))

    started_at = time.time()
    for p in processes:
        p.start()

    try:
        while True:
            time.sleep(2)
            live_processes = 0
            for p in processes:
                if p.is_alive():
                    live_processes += 1
                    print("Process {} is alive.".format(p.pid))
            if live_processes == 0:
                break

        # Moving files to a new location
        print("Moving video to streaming  directory...")
        if os.path.isfile(output_video):
            new_path = output_video.replace(video_making_path, streaming_path)
            os.rename(output_video, new_path)

        # Remove session directory
        print("Removing processing directory...")
        shutil.rmtree(session_path)

        print("Done")

        print("Recording session finished after {} seconds.".format(time.time() - started_at))
    except:
        # Remove the whole session directory
        print("Directory {} has been removed, due to errors.".format(session_path))
        #shutil.rmtree(session_path)


if __name__ == "__main__":
    run_main()
