#!/usr/bin/env python3
import time
import multiprocessing as mp
import cv2
import os
import signal
import shutil
import subprocess
from typing import List

from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions
from Recorder.VideoRecorder import VideoRecorder
from ActivityDetector.Detector import Detector
from Shared.Camera import Camera


def start_single_camera(camera_id: int, source: str, fps: int, width: int, height: int, client: int,
                        building: int, playground: int, target_path: str,
                        start_of_capture: time, end_of_capture: time, ai_queue: mp.Queue):

    camera = Camera(camera_id, source, fps, width, height,
                    client, building, playground, target_path, start_of_capture, end_of_capture)

    video = VideoRecorder(camera, ai_queue)
    video.start()


def play_video(ffmpeg_utility_path, camera_id: int, source: str, fps: int, playtime: int, frames_to_skip: int):
    cmd = [ffmpeg_utility_path,
           "-r", str(fps),
           "-re",
           "-i", source,
           "-map", "0:v",
           "input_format", "mjpeg",
           "-ss", round(float(frames_to_skip) / fps, 2),
           "-t", playtime,
           "-pix_fmt", "yuyv422",
           "-f", "v4l2",
           "/dev/video{video_id}".format(video_id=camera_id - 1),
           "|", "tee", "video{video_id}.log".format(video_id=camera_id - 1),
           ]

    p = subprocess.Popen(" ".join(cmd), stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
    return p


def create_fake_camera_loopback(cameras):
    if not os.path.ismount(os.path.normpath("/dev/video{}".format(cameras - 1))):
        print("Mounting fake cameras...")
        process = subprocess.Popen("sudo modprobe -r v4l2loopback", shell=True, stdout=subprocess.PIPE)
        process.wait()
        process = subprocess.Popen("sudo modprobe v4l2loopback devices={cameras}".format(cameras=cameras),
                                   shell=True, stdout=subprocess.PIPE)
        process.wait()


def start_activity_detection(playground: int, ai_queues: list):
    Detector(playground, ai_queues)
    pass


def run_main():
    config = Configuration()

    # Schedule the start and end of capture 3 seconds ahead, so that all camera start at the same time
    playtime = int(config.common["playtime"])
    start_of_capture = time.time() + 10
    end_of_capture = start_of_capture + playtime
    ffmpeg_utility_path = os.path.normpath(r"{}/{}".format(os.getcwd(),
                                                           config.video_maker["ffmpeg-utility-full-path"]))
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
    players = []
    i = 0

    # Get main configuration settings
    client = int(config.common["client"])
    building = int(config.common["building"])
    playground = int(config.common["playground"])
    fps = int(config.recorder["fps"])

    # Ensure session directory exists
    session_path = SharedFunctions.get_recording_path(root_recording_path, building, playground, start_of_capture)
    SharedFunctions.ensure_directory_exists(session_path)

    # Mount fake cameras, if they don't exist
    if ".mp4" in video_addresses:
        create_fake_camera_loopback(len(video_addresses))

    for v in video_addresses:
        i += 1
        ai_queue = mp.Queue()
        ai_queues.append(ai_queue)

        # Ensure video_delays array is initialised
        if len(frames_to_skip) != i:
            frames_to_skip.append("0")
            
        # If video source is not camera, but mp4 file, fix the path
        source_path = v
        if ".mp4" in v:
            source_path = os.path.normpath(r"/dev/video{}".format(i - 1))
            players.append(play_video(ffmpeg_utility_path, i, source_path, fps, playtime, int(frames_to_skip[i - 1])))

        # Ensure directory for particular camera exists
        camera_path = os.path.normpath(r"{}/{}".format(session_path, i))
        SharedFunctions.ensure_directory_exists(camera_path)

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
                                          ai_queue)))

    processes.append(mp.Process(target=start_activity_detection, args=(playground, ai_queues)))

    started_at = time.time()
    for p in processes:
        p.start()

    try:
        for p in processes:
            p.join()

        for p in players:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)

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
