#!/usr/bin/env python3
from multiprocessing import connection, Pipe, Process
import time
import os
import shutil
import threading
import argparse
import socket
import errno
import psutil
from typing import List
from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions
from Recorder.VideoRecorder import VideoRecorder
from ActivityDetector.Detector import Detector
from Shared.Camera import Camera
from VideoMaker.VideoMaker import VideoMaker
from Shared.DefinedPolygon import DefinedPolygon
from Uploaders.FtpUploader import FtpUploader
from Shared.RecordScreenInfo import RecordScreenInfo
from Shared.EasyTerminal import EasyTerminal
from Shared.RecordScreenInfoEventItem import RecordScreenInfoEventItem
from Shared.LogHandler import LogHandler
from Shared.RecordScreenInfoOperation import RecordScreenInfoOperation


class Record(object):
    def __init__(self, hour: int, minute: int):
        #p = psutil.Process()
        #p.cpu_affinity(0)
        self.config = Configuration()
        self.dispatching = True
        self.dumping_screen_information = True
        self.dispatching_lock = threading.Lock()
        self.dumping_screen_information_lock = threading.Lock()
        self.terminal = EasyTerminal()
        self.screen_info = RecordScreenInfo(self.terminal)
        self.planned_start_time = SharedFunctions.planned_start_time(hour, minute)
        self.logger = LogHandler("recorder",
                                 self.planned_start_time,
                                 self.planned_start_time + int(self.config.common["playtime"]))

    @staticmethod
    def start_single_camera(camera: Camera, ai_frame_connection: connection.Connection,
                            video_frame_connection: connection.Connection,
                            screen_connection: connection.Connection,
                            detection_pipe_in: connection.Connection,
                            debugging: bool):

        video = VideoRecorder(camera, ai_frame_connection, video_frame_connection, screen_connection,
                              detection_pipe_in, debugging)
        video.start()

    @staticmethod
    def start_activity_detection(playground: int, ai_frame_connections: List[connection.Connection],
                                 class_id: int,
                                 network_config: str, network_weights: str, coco_config: str,
                                 width: int, height: int,
                                 detection_connections: List[connection.Connection], cameras: List[Camera],
                                 polygons: List[DefinedPolygon], screen_connection: connection.Connection,
                                 debugging: bool, number_of_cameras: int):

        detector = Detector(playground, ai_frame_connections, class_id,
                            network_config, network_weights,
                            coco_config, width, height, cameras, detection_connections,
                            polygons, screen_connection, debugging, number_of_cameras)

        detector.start()

    @staticmethod
    def start_video_making(playground: int, video_frame_connections: List[connection.Connection], output_video: str,
                           latency: float, detection_connection: connection.Connection,
                           polygons: List[DefinedPolygon], width: int, height: int, fps: int,
                           screen_connection: connection.Connection, debugging: bool):
        video_maker = VideoMaker(playground, video_frame_connections, output_video, latency,
                                 detection_connection, polygons, width, height, fps, screen_connection, debugging)
        video_maker.start()

    def start(self, debugging: bool):
        # Schedule the start and end of capture 3 seconds ahead, so that all camera start at the same time
        latency = int(self.config.recorder["latency"])
        delay_recording_start = int(self.config.recorder["delay-recording-start"])
        playtime = int(self.config.common["playtime"])
        start_of_capture = time.time() + delay_recording_start
        end_of_capture = start_of_capture + playtime + (latency / 1000)
        video_latency = float(self.config.video_maker["save-delay"])
        video_addresses = str(self.config.recorder["video"]).split(",")

        # Ensure that root directory exists
        dump_path = os.path.normpath(r"{}".format(self.config.common["dump-path"]))
        SharedFunctions.ensure_directory_exists(dump_path)

        # Ensure that recording directory exists
        recording_path = os.path.join(dump_path, self.config.recorder["recording-path"])
        SharedFunctions.ensure_directory_exists(recording_path)

        # Ensure that video making directory exists
        video_making_path = os.path.join(dump_path, self.config.video_maker["video-making-path"])
        SharedFunctions.ensure_directory_exists(video_making_path)

        # Ensure that streaming directory exists
        streaming_path = os.path.join(dump_path, self.config.video_maker["streaming-path"])
        SharedFunctions.ensure_directory_exists(streaming_path)

        # Ensure that file storage for temporarely saving frames exists
        SharedFunctions.ensure_directory_exists("/tmp/sports-replay")

        processes = []
        i = 0

        # Get main configuration settings
        playground = int(self.config.common["playground"])
        fps = int(self.config.recorder["fps"])
        cdfps = float(self.config.activity_detector["cdfps"])
        width = int(self.config.recorder["width"])
        height = int(self.config.recorder["height"])
        rtsp_user = self.config.recorder["rtsp-user"]
        rtsp_password = self.config.recorder["rtsp-password"]
        network_config = os.path.join(os.getcwd(), self.config.activity_detector["network-config"])
        network_weights = os.path.join(os.getcwd(), self.config.activity_detector["network-weights"])
        coco_config = os.path.join(os.getcwd(), self.config.activity_detector["coco-config"])
        coco_labels = os.path.join(os.getcwd(), self.config.activity_detector["coco-labels"])
        class_id = SharedFunctions.get_class_id(coco_labels, self.config.activity_detector["sports-ball"])
        polygons_path = os.path.normpath(r"{}".format(self.config.activity_detector["polygons"]))
        polygons_json = SharedFunctions.read_text_file(polygons_path)
        pi_host = self.config.tv_box["host"]
        pi_ftp_username = self.config.tv_box["user"]
        pi_ftp_password = self.config.tv_box["password"]

        # Initialise the polygons (for covered, and restricted areas).
        polygons: List[DefinedPolygon] = DefinedPolygon.get_polygons(polygons_json)

        # Ensure session directory exists
        session_path = SharedFunctions.get_recording_path(recording_path,
                                                          playground,
                                                          self.planned_start_time)
        SharedFunctions.ensure_directory_exists(session_path)

        # Get output video path
        output_video = SharedFunctions.get_output_video(video_making_path, playground, self.planned_start_time)

        # Define the pipes, for the communication between the processes
        video_maker_detection_pipe_in, video_maker_detection_pipe_out = Pipe(duplex=False)
        detector_screen_pipe_in, detector_screen_pipe_out = Pipe(duplex=False)
        video_maker_screen_pipe_in, video_maker_screen_pipe_out = Pipe(duplex=False)
        dumping_screen_information_pipes = [detector_screen_pipe_in, video_maker_screen_pipe_in]
        video_frame_pipes_in = []
        ai_frame_pipes_in = []
        video_frame_pipes_out = []
        ai_frame_pipes_out = []
        detection_pipes_in = []
        detection_pipes_out = [video_maker_detection_pipe_out]
        cameras = []

        # For each camera defined in the settings, generate one process
        for v in video_addresses:
            i += 1
            # If video source is not camera, but the video file, fix the path
            if ".mp4" in v:
                source_path = "filesrc location={location} latency={latency} " \
                              "! qtdemux " \
                              "! queue " \
                              "! h264parse " \
                              "! nvv4l2decoder enable-max-performance=1 drop-frame-interval=1 " \
                              "! nvvidconv " \
                              "! video/x-raw(memory:NVMM),format=BGRx,width={width},height={height} " \
                              "! queue " \
                              "! nvvidconv " \
                              "! video/x-raw,format=BGRx" \
                              "! videoconvert " \
                              "! video/x-raw,format=BGR " \
                              "! videorate skip-to-first=1 qos=0 average-period=0000000000 max-rate={fps} " \
                              "! capsfilter caps='video/x-raw,framerate={fps}/1' " \
                              "! appsink sync=0".format(location=os.path.normpath(r"{}".format(v)),
                                                        fps=fps,
                                                        width=width,
                                                        height=height,
                                                        latency=latency)
            else:
                source_path = "rtspsrc location={location} latency={latency} " \
                              "user-id={user} user-pw={password} " \
                              "! queue " \
                              "! rtph264depay " \
                              "! h264parse " \
                              "! nvv4l2decoder enable-max-performance=1 drop-frame-interval=1 " \
                              "! nvvidconv " \
                              "! video/x-raw(memory:NVMM),format=BGRx,width={width},height={height} " \
                              "! queue " \
                              "! nvvidconv " \
                              "! video/x-raw,format=BGRx" \
                              "! videoconvert " \
                              "! video/x-raw,format=BGR " \
                              "! videorate max-rate={fps} drop-only=true average-period=5000000 " \
                              "! video/x-raw,framerate={fps}/1 " \
                              "! appsink sync=true".format(location=v,
                                                           fps=fps,
                                                           width=width,
                                                           height=height,
                                                           latency=latency,
                                                           user=rtsp_user,
                                                           password=rtsp_password)

            # Define the camera, and add it to the list of cameras
            camera = Camera(i, source_path, fps, cdfps, width, height,
                            playground, session_path, self.planned_start_time, start_of_capture, end_of_capture)
            cameras.append(camera)

            # Add pipe connection for dumping screen messages
            camera_screen_pipe_in, camera_screen_pipe_out = Pipe(duplex=False)
            dumping_screen_information_pipes.append(camera_screen_pipe_in)

            # Add pipe connection for recorded frames to be sent to video maker
            video_frame_pipe_in, video_frame_pipe_out = Pipe(duplex=False)
            video_frame_pipes_in.append(video_frame_pipe_in)
            video_frame_pipes_out.append(video_frame_pipe_out)

            ai_frame_pipe_in, ai_frame_pipe_out = Pipe(duplex=False)
            ai_frame_pipes_in.append(ai_frame_pipe_in)
            ai_frame_pipes_out.append(ai_frame_pipe_out)

            detection_pipe_in, detection_pipe_out = Pipe(duplex=False, )
            detection_pipes_in.append(detection_pipe_in)
            detection_pipes_out.append(detection_pipe_out)

            # Start recording
            processes.append(Process(target=self.start_single_camera,
                                     args=(camera,
                                           ai_frame_pipe_out,
                                           video_frame_pipe_out,
                                           camera_screen_pipe_out,
                                           detection_pipe_in,
                                           debugging)))

        # Create a process for activity detection
        processes.append(Process(target=self.start_activity_detection,
                                 args=(playground, ai_frame_pipes_in, class_id, network_config, network_weights,
                                       coco_config, width, height, detection_pipes_out, cameras,
                                       polygons, detector_screen_pipe_out, debugging,
                                       len(video_addresses))))

        # Create a process for video rendering
        processes.append(Process(target=self.start_video_making,
                                 args=(playground, video_frame_pipes_in, output_video, video_latency,
                                       video_maker_detection_pipe_in, polygons, width, height, fps,
                                       video_maker_screen_pipe_out, debugging)))

        # Start the processes
        started_at = time.time()
        for p in processes:
            p.start()

        while time.time() > start_of_capture:
            pass

        self.screen_info.refresh()

        # Start thread that deals with pipes, i.e. dispatches the messages
        dispatch_thread = threading.Thread(target=self.dispatch_detection_messages,
                                           args=(detection_pipe_in, video_maker_detection_pipe_out))
        dispatch_thread.start()
        dump_information_thread = threading.Thread(target=self.dump_screen_information,
                                                   args=(dumping_screen_information_pipes,))
        dump_information_thread.start()

        try:
            while True:
                time.sleep(2)
                live_processes = 0
                for p in processes:
                    if p.is_alive():
                        live_processes += 1

                self.logger.info(RecordScreenInfoEventItem(RecordScreenInfo.LIVE_PROCESSES,
                                                           RecordScreenInfoOperation.SET,
                                                           str(live_processes)))

                if live_processes == 0:
                    break
                else:
                    if len(processes) != live_processes:
                        self.screen_info.set_item_value(RecordScreenInfo.LIVE_PROCESSES, str(live_processes))

            # Moving files to a new location
            self.logger.info(RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                                       RecordScreenInfoOperation.SET,
                                                       "Uploading video to Raspberry Pi..."))

            if os.path.isfile(output_video):
                uploader = FtpUploader(pi_host, pi_ftp_username, pi_ftp_password)
                uploader.upload(output_video, os.path.basename(os.path.normpath(output_video)), True)
                os.remove(output_video)

            # Remove session directory
            self.logger.info(RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                                       RecordScreenInfoOperation.SET,
                                                       "Removing processing directories..."))
            if not debugging:
                self.files_cleanup(session_path, streaming_path, video_making_path)

            self.logger.info(RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                                       RecordScreenInfoOperation.SET,
                                                       "Recording session finished after {} seconds.".
                                                       format(time.time() - started_at)))

            self.logger.info(RecordScreenInfoEventItem(RecordScreenInfo.COMPLETED,
                                                       RecordScreenInfoOperation.SET,
                                                       ""))
            # Stop pipe connection functions
            with self.dispatching_lock:
                self.dispatching = False
            dispatch_thread.join()
            with self.dumping_screen_information_lock:
                self.dumping_screen_information = False
            dump_information_thread.join()

            SharedFunctions.close_connection(video_maker_detection_pipe_in)
            SharedFunctions.close_connection(video_maker_detection_pipe_out)
            SharedFunctions.close_connection(detector_screen_pipe_in)
            SharedFunctions.close_connection(detector_screen_pipe_out)
            SharedFunctions.close_connection(video_maker_screen_pipe_in)
            SharedFunctions.close_connection(video_maker_screen_pipe_out)

            for conn in detection_pipes_out:
                SharedFunctions.close_connection(conn)
            for conn in detection_pipes_in:
                SharedFunctions.close_connection(conn)
            for conn in ai_frame_pipes_in:
                SharedFunctions.close_connection(conn)
            for conn in ai_frame_pipes_out:
                SharedFunctions.close_connection(conn)
            for conn in video_frame_pipes_in:
                SharedFunctions.close_connection(conn)
            for conn in video_frame_pipes_out:
                SharedFunctions.close_connection(conn)
        except Exception as ex:
            self.dispatching = False
            self.dumping_screen_information = False

            if not debugging:
                # Remove the whole session directory
                self.logger.info(RecordScreenInfoEventItem(RecordScreenInfo.CURRENT_TASK,
                                                           RecordScreenInfoOperation.SET,
                                                           "Directory {} has been removed, due to errors."
                                                           .format(session_path)))

                self.files_cleanup(session_path, streaming_path, video_making_path)

    @staticmethod
    def files_cleanup(session_path: str, streaming_path: str, video_making_path: str):
        shutil.rmtree(session_path)
        shutil.rmtree(streaming_path)
        shutil.rmtree(video_making_path)

    def dispatch_detection_messages(self, incoming_connection: connection.Connection,
                                    outgoing_connection: connection.Connection):
        dispatching = True
        active_camera_id = 1
        while dispatching:
            with self.dispatching_lock:
                dispatching = self.dispatching

            try:
                # If there is any incoming message
                if incoming_connection.poll():
                    # Receive the message
                    detection = incoming_connection.recv()

                    # If there is a change in camera activity, remember that, and dispatch the message to
                    # VideoMaker processes
                    if detection.camera_id != active_camera_id:
                        active_camera_id = detection.camera_id
                        outgoing_connection.send(detection)
            except EOFError:
                pass
            except socket.error as e:
                pass
            finally:
                pass

        # Do the cleanup
        try:
            SharedFunctions.close_connection(incoming_connection)
            SharedFunctions.close_connection(outgoing_connection)
        except EOFError:
            pass
        except socket.error as e:
            pass

    def dump_screen_information(self, incoming_connections: List[Pipe]):
        dumping_screen_information = True
        while dumping_screen_information:
            with self.dumping_screen_information_lock:
                dumping_screen_information = self.dumping_screen_information

            try:
                for incoming_connection in incoming_connections:
                    # If there is any incoming message
                    if incoming_connection.poll():
                        # Receive the message
                        events: List[RecordScreenInfoEventItem] = incoming_connection.recv()

                        for information in events:
                            if information.operation == RecordScreenInfoOperation.ADD:
                                self.screen_info.increment_item_value(information.type, information.value)
                            else:
                                self.screen_info.set_item_value(information.type, information.value)

                            if information.type == RecordScreenInfo.ERROR_LOG:
                                self.logger.error(information)
                            else:
                                self.logger.info(information)
            except EOFError:
                pass
            except socket.error as e:
                if e.errno != errno.EPIPE:
                    print(SharedFunctions.get_exception_info(e))
            finally:
                pass

        # Post the remaining logs to the back-end server, and terminate posting thread
        self.logger.stop_posting()

        # Do the cleanup
        try:
            for incoming_connection in incoming_connections:
                SharedFunctions.close_connection(incoming_connection)
        except EOFError:
            pass
        except socket.error as e:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sports Replay Recorder",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog="Please run using: python3 Record.py "
                                            "--hour=HH --minute=MM --debug=1")

    parser.add_argument("--debug", type=int, default=0, help="True for debugging.")
    parser.add_argument("--hour", type=int, help="Starting hour", required=True)
    parser.add_argument("--minute", type=int, help="Starting minute.", required=True)
    opt, argv = parser.parse_known_args()
    Record(opt.hour, opt.minute).start(opt.debug == 1)
