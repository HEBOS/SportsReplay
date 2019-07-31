import time
import os
import shutil
from typing import List
from Shared.SharedFunctions import SharedFunctions
from Shared.CameraJson import CameraJson


class VideoMakerEngine(object):
    def __init__(self):
        time.sleep(1)

    @staticmethod
    def process(directory: str, number_of_cameras: int):
        # remove READY.TXT, so it cannot be picked up by another instance of this script
        SharedFunctions.remove_flag_file(directory)

        # Create an empty list large enough to hold all camera lists
        cameras = [List[str]]*number_of_cameras

        # Fill the list (i.e. every item of the list will be the camera that has a number of jpg files)
        for i in range(1, number_of_cameras):
            jpg_files: List[str] = [SharedFunctions.get_file_name_only(fi)+".jpg" for fi in os.listdir(directory)
                                    if os.path.isfile(os.path.join(directory, fi)) and fi.lower().endswith(".jpg")]
            cameras[i] = jpg_files

        # Get intersection of all files, so we can go from the first one to the last one
        all_files: List[str] = list(set.intersection(*map(set, cameras)))

        # Sort the list
        all_files.sort()

        # Initialise the values that will be replaced below
        active_camera = 1
        last_activation = 0
        last_activation_ball_size = 0

        # Create an empty list of CameraJson objects with length to support the number of cameras we deal with
        json_files_to_check = [List[CameraJson]]

        # Create an empty list that will hold all files, from which the final video will be created
        video_file_input_list = []

        # Loop through the sorted list of the files
        for file_name in all_files:
            # Find first json file, and set that camera as an active one
            for i in range(1, number_of_cameras):
                # Determine the full json path
                json_file_path = \
                    os.path.normpath("{}/{}/{}.json".format(directory,
                                                            i,
                                                            SharedFunctions.get_file_name_only(file_name)))
                # If file exists add the new CameraJson object file to the list of candidates that will be examined
                if os.path.isfile(json_file_path):
                    json_files_to_check.append(CameraJson(i, json_file_path))

            # Now that we have all candidates that need to be examined, determine if there is any change to
            # active camera, and update last activation accordingly
            active_camera, last_activation, last_activation_ball_size = \
                VideoMakerEngine.determine_active_camera(json_files_to_check, active_camera,
                                                         last_activation, last_activation_ball_size)

            # Copy the corresponding file from the active camera directory to the list of files from which
            # FFMPEG utility will create the video
            jpg_file_path = \
                os.path.normpath("{}/{}/{}.jpg".format(directory,
                                                       active_camera,
                                                       SharedFunctions.get_file_name_only(file_name)))
            video_file_input_list.append(jpg_file_path)

            print(video_file_input_list)

    @staticmethod
    def determine_active_camera(json_files_to_check: List[CameraJson], active_camera: int,
                                last_activation: float, last_activation_ball_size: int) -> (int, float, int):
        # Activation can take place only if at least one second has elapsed
        if last_activation < 1:
            return active_camera, last_activation, last_activation_ball_size
        else:
            # If we have only one json to check, it means the ball is there, so we take that camera as an active one
            if len(json_files_to_check) == 1:
                return json_files_to_check[0].camera_id, time.time(), last_activation_ball_size
            else:
                # Preserve the current state of the detection
                current_state = (active_camera, last_activation_ball_size)
                # Check all cameras
                for json_file_to_check in json_files_to_check:
                    # Determine the state of the frame of the next checked camera
                    peeked_state = (json_file_to_check.camera_id, json_file_to_check.get_ball_size())
                    # if the frame contains a larger ball, set newly detected state to be the current state
                    if peeked_state[1] > current_state[1]:
                        current_state = peeked_state

                # Return new state (camera, time, ball size)
                return current_state[0], json_files_to_check[0].get_time(), current_state[1]

