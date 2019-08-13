#!/usr/bin/env python3
import time
import cv2
import os
from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions
from VideoMaker.VideoMakerEngine import VideoMakerEngine


def run_main():
    config = Configuration()

    # Get main configuration settings
    client = int(config.common["client"])
    building = int(config.common["building"])
    playground = int(config.common["playground"])

    # Ensure that root recording directory exists.
    root_recording_path = os.path.join(config.common["dump-path"], config.recorder["recording-path"])
    SharedFunctions.ensure_directory_exists(root_recording_path)

    # Ensure that root post recording directory exists.
    root_post_recording_path = os.path.join(config.common["dump-path"], config.post_recorder["post-recording-path"])
    SharedFunctions.ensure_directory_exists(root_post_recording_path)

    # Ensure that root video making directory exists
    video_making_path = os.path.join(config.common["dump-path"], config.video_maker["video-making-path"])
    SharedFunctions.ensure_directory_exists(video_making_path)

    # Ensure that streaming directory exists
    streaming_path = os.path.join(config.common["dump-path"], config.video_maker["streaming-path"])
    SharedFunctions.ensure_directory_exists(streaming_path)

    # Get ffmpeg utility path
    ffmpeg_utility_path = os.path.normpath(config.video_maker["ffmpeg-utility-full-path"])

    # Get fps of output video
    fps = config.recorder["fps"]
    video_addresses = str(config.recorder["video"]).split(",")
    number_of_cameras = len(video_addresses)
    stopped = False

    while not stopped:
        # Get first directory in root post recording sub-directory.
        directories = [dI for dI in os.listdir(root_post_recording_path)
                       if os.path.isdir(os.path.join(root_post_recording_path, dI))]

        if len(directories) > 0:
            directory = directories[0]

            # Wait max 1 minute for READY.TXT to appear in the directory.
            flag_file = os.path.normpath(r"{}/{}/READY.TXT").format(root_post_recording_path, directory)
            started_waiting = time.time()
            while not os.path.isfile(flag_file):
                time.sleep(1)
                if time.time() - started_waiting > 60:
                    break

            # If file appeared eventually, start video making process.
            if os.path.isfile(flag_file):
                # Move directory to directory where video maker will output files
                full_directory_path = os.path.normpath(r"{}/{}").format(root_post_recording_path, directory)
                new_path = full_directory_path.replace(root_post_recording_path, video_making_path)
                os.rename(full_directory_path, new_path)

                # Start video maker engine
                VideoMakerEngine().process(new_path,
                                           number_of_cameras,
                                           fps,
                                           directory,
                                           streaming_path,
                                           ffmpeg_utility_path)
        else:
            print("No recordings to process. Pausing for 5 seconds.")
            time.sleep(5)

        k = cv2.waitKey(100)
        if k == 27:
            print("VideoMaker has been terminated.")
            stopped = True


if __name__ == "__main__":
    run_main()
