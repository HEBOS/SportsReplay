#!/usr/bin/env python3
import multiprocessing as mp
import time
import os
import shutil
import threading
import argparse
from typing import List
from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions
from Recorder.VideoRecorder import VideoRecorder
from ActivityDetector.Detector import Detector
from Shared.Camera import Camera
from VideoMaker.VideoMaker import VideoMaker
from Shared.MultiProcessingQueue import MultiProcessingQueue
from Shared.DefinedPolygon import DefinedPolygon
from Uploaders.FtpUploader import FtpUploader


class Record(object):
    def __init__(self):
        self.dispatching = True
        self.dispatch_lock = threading.Lock()

    def start_single_camera(self, camera: Camera, ai_queue: MultiProcessingQueue, video_queue: MultiProcessingQueue,
                            debugging: bool):

        video = VideoRecorder(camera, ai_queue, video_queue, debugging)
        video.start()

    def start_activity_detection(self, playground: int, ai_queue: MultiProcessingQueue,
                                 video_queue: MultiProcessingQueue, class_id: int,
                                 network_config: str, network_weights: str, coco_config: str,
                                 width: int, height: int,
                                 detection_connection: mp.connection.Connection, cameras: List[Camera],
                                 polygons: List[DefinedPolygon], debugging: bool):

        detector = Detector(playground, ai_queue, video_queue, class_id, network_config, network_weights,
                            coco_config, width, height, cameras, detection_connection,
                            polygons, debugging)

        detector.start()

    def start_video_making(self, playground: int, video_queue: MultiProcessingQueue, output_video: str,
                           start_of_video_saving: float, detection_connection: mp.connection.Connection,
                           polygons: List[DefinedPolygon], width: int, height: int, fps: int, debugging: bool):
        video_maker = VideoMaker(playground, video_queue, output_video, start_of_video_saving,
                                 detection_connection, polygons, width, height, fps, debugging)
        video_maker.start()

    def start(self, debugging):
        config = Configuration()

        # Schedule the start and end of capture 3 seconds ahead, so that all camera start at the same time
        playtime = int(config.common["playtime"])
        start_of_capture = time.time() + 15
        end_of_capture = start_of_capture + 15 + playtime
        start_of_video_saving = time.time() + 15 + float(config.video_maker["save-delay"])
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

        # Create queues and lists
        ai_queue = MultiProcessingQueue(maxsize=10)
        video_queue = MultiProcessingQueue(maxsize=100)
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
        rtsp_user = config.recorder["rtsp-user"]
        rtsp_password = config.recorder["rtsp-password"]
        network_config = os.path.join(os.getcwd(), config.activity_detector["network-config"])
        network_weights = os.path.join(os.getcwd(), config.activity_detector["network-weights"])
        coco_config = os.path.join(os.getcwd(), config.activity_detector["coco-config"])
        coco_labels = os.path.join(os.getcwd(), config.activity_detector["coco-labels"])
        class_id = SharedFunctions.get_class_id(coco_labels, config.activity_detector["sports-ball"])
        polygons_path = os.path.normpath(r"{}".format(config.activity_detector["polygons"]))
        polygons_json = SharedFunctions.read_text_file(polygons_path)
        pi_host = config.pi_computer["host"]
        pi_ftp_username = config.pi_computer["user"]
        pi_ftp_password = config.pi_computer["password"]

        # Initialise the polygons (for covered, and restricted areas).
        polygons: List[DefinedPolygon] = DefinedPolygon.get_polygons(polygons_json)

        # Ensure session directory exists
        session_path = SharedFunctions.get_recording_path(recording_path, building, playground, start_of_capture)
        SharedFunctions.ensure_directory_exists(session_path)

        # Get output video path
        output_video = SharedFunctions.get_output_video(video_making_path, building, playground, start_of_capture)

        # Define the pipes, for the communication between the processes
        detection_pipe_in, detection_pipe_out = mp.Pipe(duplex=False)
        video_maker_pipe_in, video_maker_pipe_out = mp.Pipe(duplex=False)

        cameras = []

        # For each camera defined in the settings, generate one process
        for v in video_addresses:
            i += 1
            # If video source is not camera, but mp4 file, fix the path
            if ".mp4" in v:
                source_path = "filesrc location={location} " \
                              "! qtdemux " \
                              "! queue " \
                              "! h264parse " \
                              "! omxh264dec " \
                              "! video/x-raw,format=NV12,width=1280,height=720,framerate={fps}/1 " \
                              "! videoconvert " \
                              "! video/x-raw,format=BGR " \
                              "! appsink sync=0".format(location=os.path.normpath(r"{}".format(v)),
                                                        fps=fps,
                                                        width=width,
                                                        height=height)

            else:
                source_path = "rtspsrc location={location} latency=0 " \
                              "! rtph264depay user-id={user} user-pw={password} " \
                              "! capsfilter caps=video/x-h264,width={width}," \
                              "height={height},framerate={fps} " \
                              "! queue " \
                              "! h264parse " \
                              "! omxh264dec " \
                              "! video/x-raw,format=NV12,width=1280,height=720,framerate={fps}/1 " \
                              "! appsink sync=0".format(location=v,
                                                        fps=fps,
                                                        width=width,
                                                        height=height,
                                                        user=rtsp_user,
                                                        password=rtsp_password)

            print(source_path)

            # Define the cammera, and add it to the list of cameras
            camera = Camera(i, source_path, fps, cdfps, width, height,
                            client, building, playground, session_path, start_of_capture, end_of_capture)
            cameras.append(camera)

            # Start recording
            processes.append(mp.Process(target=self.start_single_camera,
                                        args=(camera,
                                              ai_queue,
                                              video_queue,
                                              debugging)))

        # Create a process for activity detection
        processes.append(mp.Process(target=self.start_activity_detection,
                                    args=(playground, ai_queue, video_queue, class_id, network_config, network_weights,
                                          coco_config, width, height, detection_pipe_out, cameras,
                                          polygons, debugging)))

        # Create a process for video rendering
        processes.append(mp.Process(target=self.start_video_making,
                                    args=(playground, video_queue, output_video, start_of_video_saving,
                                          video_maker_pipe_in, polygons, width, height, fps, debugging)))

        # Start the processes
        started_at = time.time()
        for p in processes:
            p.start()

        # Start thread that deals with pipes, i.e. dispatches the messages
        dispatch_thread = threading.Thread(target=self.dispatch_detection_messages,
                                           args=(detection_pipe_in, video_maker_pipe_out))
        dispatch_thread.start()

        try:
            while True:
                time.sleep(2)
                live_processes = 0
                for p in processes:
                    if p.is_alive():
                        live_processes += 1
                if live_processes == 0:
                    # Stop dispatch detection thread
                    with self.dispatch_lock:
                        self.dispatching = False
                    break
                else:
                    if len(processes) != live_processes:
                        print("There are {}/{} processes still executing...".format(live_processes, len(processes)))

            # Wait for dispatch_detection_messages to complete
            dispatch_thread.join()

            # Moving files to a new location
            print("Uploading video to Raspberry Pi")
            if os.path.isfile(output_video):
                uploader = FtpUploader(pi_host, pi_ftp_username, pi_ftp_password)
                uploader.upload(output_video, os.path.basename(os.path.normpath(output_video)), True)
                os.remove(output_video)

            # Remove session directory
            print("Removing processing directories...")
            if not debugging:
                self.files_cleanup(session_path, streaming_path, video_making_path)

            print("Done")
            print("Recording session finished after {} seconds.".format(time.time() - started_at))
        except:
            # Remove the whole session directory
            print("Directory {} has been removed, due to errors.".format(session_path))
            if not debugging:
                self.files_cleanup(session_path, streaming_path, video_making_path)

    def files_cleanup(self, session_path: str, streaming_path: str, video_making_path: str):
        shutil.rmtree(session_path)
        shutil.rmtree(streaming_path)
        shutil.rmtree(video_making_path)

    def dispatch_detection_messages(self, incomming_connection: mp.connection.Connection,
                                    outgoing_connection: mp.connection.Connection):
        dispatching = True
        active_camera_id = 1
        while dispatching:
            with self.dispatch_lock:
                dispatching = self.dispatching

            try:
                # If there is any incomming message
                if incomming_connection.poll():
                    # Receive the message
                    detection = incomming_connection.recv()

                    # If there is a change in camera activity, remember that, and dispatch the message to
                    # VideoMaker processes
                    if detection.camera_id != active_camera_id:
                        active_camera_id = detection.camera_id
                        outgoing_connection.send(detection)
            finally:
                pass

        # Do the cleanup
        incomming_connection.close()
        outgoing_connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sports Replay Recorder.",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog="Please run using: python3 Recorder.py --debug true")

    parser.add_argument("--debug", type=int, default=0, help="True for debugging.")
    opt, argv = parser.parse_known_args()
    Record().start(opt.debug == 1)
