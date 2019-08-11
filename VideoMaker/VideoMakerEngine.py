#!/usr/bin/env python3
import time
import os
import shutil
import subprocess
from typing import List
from Shared.SharedFunctions import SharedFunctions
from Shared.CameraJson import CameraJson


class VideoMakerEngine(object):
    def __init__(self):
        time.sleep(1)
        self.detection_log: List[str] = []

    def process(self, directory: str, number_of_cameras: int, fps: int,
                session_name: str, stream_directory: str, ffmpeg_utility_path: str):
        # remove READY.TXT, so it cannot be picked up by another instance of this script
        SharedFunctions.remove_flag_file(directory)

        # Create an empty list large enough to hold all camera lists
        cameras: List[List[str]] = [List[str]]*number_of_cameras

        all_files = set()

        # Fill the list (i.e. every item of the list will be the camera that has a number of jpg files)
        for i in range(0, number_of_cameras):
            # Get all jpg files in the camera directory
            camera_directory = os.path.normpath(r"{}/{}".format(directory, i + 1))
            cameras[i] = [SharedFunctions.get_file_name_only(fi)+".jpg"
                          for fi in os.listdir(camera_directory)
                          if os.path.isfile(os.path.join(camera_directory, fi)) and fi.lower().endswith(".jpg")]

            # Get intersection of all files, so we can go from the first one to the last one
            if len(all_files) == 0:
                all_files = set(cameras[i])
            else:
                all_files = set.intersection(all_files, cameras[i])

        # Sort the list
        sorted_files = sorted(list(all_files))

        # Initialise the values that will be replaced below
        active_camera: int = 1
        last_activation: float = 0
        last_activation_ball_size: int = 0

        # Create an empty list that will hold all files, from which the final video will be created
        video_file_input_list = []

        # Loop through the sorted list of the files
        for file_name in sorted_files:
            # Create an empty list of CameraJson objects with length to support the number of cameras we deal with
            json_files_to_check: List[CameraJson] = []

            # Find first json file, and set that camera as an active one
            for i in range(0, number_of_cameras):
                # Determine the full json path
                json_file_path = \
                    os.path.normpath("{}/{}/{}.json".format(directory,
                                                            i + 1,
                                                            SharedFunctions.get_file_name_only(file_name)))
                # If file exists add the new CameraJson object file to the list of candidates that will be examined
                if os.path.isfile(json_file_path):
                    print("Checking ball activity in file {}".format(json_file_path))
                    json_files_to_check.append(CameraJson(i + 1, json_file_path))

            if len(json_files_to_check) > 0:
                # Now that we have all candidates that need to be examined, determine if there is any change to
                # active camera, and update last activation accordingly
                active_camera, last_activation, last_activation_ball_size = \
                    self.determine_active_camera(json_files_to_check,
                                                 active_camera,
                                                 last_activation,
                                                 last_activation_ball_size)

            # Copy the corresponding file from the active camera directory to the list of files from which
            # FFMPEG utility will create the video
            jpg_file_path = \
                os.path.normpath("{}/{}/{}.jpg".format(directory,
                                                       active_camera,
                                                       SharedFunctions.get_file_name_only(file_name)))
            video_file_input_list.append("file '{}'".format(jpg_file_path))

        # Dump vide_file_input_list into the txt file, which will be used by ffmpeg utility as an imput
        ffmpeg_input_path = os.path.normpath(r"{}/{}.txt".format(directory, session_name))
        SharedFunctions.create_list_file(ffmpeg_input_path, video_file_input_list)

        # Dump log to detection log file
        detection_log_path = os.path.normpath(r"{}/{}.log".format(directory, session_name))
        SharedFunctions.create_list_file(detection_log_path, self.detection_log)

        # Get output stream file name
        ffmpeg_video_file_path = os.path.normpath(r"{}/{}.mp4".format(stream_directory, session_name))

        # Finally create a video
        subprocess.run([ffmpeg_utility_path,
                        "-f",
                        "concat",
                        "-safe",
                        "0",
                        "-r",
                        fps,
                        "-i",
                        ffmpeg_input_path,
                        ffmpeg_video_file_path])

        print("Finished creating video for session {}".format(session_name))

    def determine_active_camera(self, json_files_to_check: List[CameraJson], active_camera: int,
                                last_activation: float, last_activation_ball_size: int) -> (int, float, int):
        # Activation can take place only if at least one second has elapsed
        current_time = json_files_to_check[0].get_time()

        if json_files_to_check[0].camera_id == 2:
            current_time = current_time

        if current_time - last_activation < 1:
            return active_camera, last_activation, last_activation_ball_size
        else:
            # If we have only one json to check, only that camera frame should be checked if there is any change in
            # activity
            if len(json_files_to_check) == 1:
                json_file_to_check: CameraJson = json_files_to_check[0]

                # Determine the state of the frame of the next checked camera
                current_ball_size = json_file_to_check.get_ball_size()

                # if the frame contains a larger ball, set newly detected state to be the current state
                if current_ball_size >= last_activation_ball_size:
                    # Create a log entry
                    self.detection_log \
                        .append("Time {} - Camera/Old Camera = [{}, {}]. Current ball size/Previous size = [{}, {}]."
                                .format(json_file_to_check.get_time(),
                                        json_file_to_check.camera_id,
                                        active_camera,
                                        current_ball_size,
                                        last_activation_ball_size))
                    return json_file_to_check.camera_id, json_file_to_check.get_time(), current_ball_size
                # Otherwise return the same information as received
                else:
                    # Create a log entry
                    self.detection_log \
                        .append("Time {} - Camera/Old Camera = [{}, {}]. Current ball size/Previous size = [{}, {}]."
                                .format(json_file_to_check.get_time(),
                                        active_camera,
                                        active_camera,
                                        current_ball_size,
                                        last_activation_ball_size))
                    return active_camera, last_activation, current_ball_size
            else:
                print("{} cameras have detected the ball.".format(len(json_files_to_check)))

                # Preserve the current state of the detection
                current_state = (active_camera, last_activation_ball_size)

                # Initially peeked state is the same as current state
                peeked_state = (active_camera, last_activation_ball_size)

                # Check all cameras
                for json_file_to_check in json_files_to_check:
                    # Determine the state of the frame of the next checked camera
                    peeked_state = (json_file_to_check.camera_id, json_file_to_check.get_ball_size())

                    # if the frame contains a larger ball, set newly detected state to be the current state
                    if peeked_state[1] >= current_state[1]:
                        current_state = peeked_state

                    # Create a log entry
                    self.detection_log \
                        .append(
                        "Time {} - Camera/Old Camera = [{}, {}]. Current ball size/Previous size = [{}, {}]."
                            .format(json_file_to_check.get_time(),
                                    current_state[0],
                                    active_camera,
                                    peeked_state[1],
                                    last_activation_ball_size))

                # Return new state (camera, time, ball size)
                return current_state[0], json_files_to_check[0].get_time(), peeked_state[1]

