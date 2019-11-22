#!/usr/bin/env python3
import time
import Shared.Camera as Camera
import numpy as np
from multiprocessing import connection
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

    @staticmethod
    def get_frame(conn: connection.Connection):
        try:
            if conn.poll():
                captured_frame = conn.recv()
                return True, captured_frame
            else:
                return False, None
        except EOFError:
            pass
        except socket.error as e:
            if e.errno != errno.EPIPE:
                # Not a broken pipe
                raise
        finally:
            pass
        return False, None

    @staticmethod
    def send_frame(conn: connection.Connection, frame):
        try:
            conn.send(frame)
        except EOFError:
            pass
        except socket.error as e:
            if e.errno != errno.EPIPE:
                # Not a broken pipe
                raise
        finally:
            pass

