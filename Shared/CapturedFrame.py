#!/usr/bin/env python3
import time
import Shared.Camera as Camera
import numpy as np
from multiprocessing import connection
from Shared.SharedFunctions import SharedFunctions
import os
import socket
import errno


class CapturedFrame(object):
    def __init__(self, camera: Camera, frame_number: int, snapshot_time: time, frame: np.array, camera_time: time):
        self.camera = camera
        self.frame_number = frame_number
        self.timestamp = int(snapshot_time) + float(frame_number / 1000)
        self.snapshot_time = snapshot_time
        self.frame = frame
        self.camera_time = camera_time

    def release(self):
        self.frame = None


class SharedCapturedFrame(object):
    def __init__(self, camera: Camera, frame_number: int, snapshot_time: time, camera_time: time, name_prefix: str,
                 size, channels: int):
        self.camera = camera
        self.frame_number = frame_number
        self.timestamp = int(snapshot_time) + float(frame_number / 1000)
        self.snapshot_time = snapshot_time
        self.camera_time = camera_time
        self.file_path = "camera-{camera}-{name_prefix}-" \
                         "{frame_number}-" \
                         "{camera_time}.npy".format(camera=camera.id,
                                                    frame_number=frame_number,
                                                    camera_time=int(self.timestamp * 1000000),
                                                    name_prefix=name_prefix)
        self.file_path = os.path.join(camera.session_path, self.file_path)
        self.channels = channels
        self.size = size


class SharedCapturedFrameHandler(object):
    @staticmethod
    def get_frame(conn: connection.Connection) -> (bool, CapturedFrame):
        try:
            if conn.poll():
                shared_captured_frame: SharedCapturedFrame = conn.recv()
                frame: np.ndarray
                if shared_captured_frame is not None:
                    if os.path.isfile(shared_captured_frame.file_path):
                        with open(shared_captured_frame.file_path, 'rb') as f:
                            image_bytes = f.read()
                            image = np.frombuffer(image_bytes, dtype=np.uint8)
                            frame = image.copy().reshape(*shared_captured_frame.size, shared_captured_frame.channels)
                            f.close()
                        captured_frame: CapturedFrame = CapturedFrame(shared_captured_frame.camera,
                                                                      shared_captured_frame.frame_number,
                                                                      shared_captured_frame.snapshot_time,
                                                                      frame,
                                                                      shared_captured_frame.camera_time)
                        os.remove(shared_captured_frame.file_path)
                        return True, captured_frame
                    else:
                        return False, None
                else:
                    return False, None
            else:
                return False, None
        except Exception as ex:
            pass
        finally:
            pass
        return False, None

    @staticmethod
    def send_frame(conn: connection.Connection, captured_frame: CapturedFrame, name_prefix):
        try:
            if captured_frame is not None:
                shared_captured_frame: SharedCapturedFrame = SharedCapturedFrame(captured_frame.camera,
                                                                                 captured_frame.frame_number,
                                                                                 captured_frame.snapshot_time,
                                                                                 captured_frame.camera_time,
                                                                                 name_prefix,
                                                                                 captured_frame.frame.shape[:2],
                                                                                 captured_frame.frame.shape[2])

                with open(shared_captured_frame.file_path, 'wb') as f:
                    f.write(captured_frame.frame.tobytes())
                    f.close()

                conn.send(shared_captured_frame)
            else:
                conn.send(None)
        except Exception as ex:
            print(SharedFunctions.get_exception_info(ex))
        except EOFError:
            pass
        except socket.error as e:
            if e.errno != errno.EPIPE:
                # Not a broken pipe
                print(SharedFunctions.get_exception_info(e))
        finally:
            pass

