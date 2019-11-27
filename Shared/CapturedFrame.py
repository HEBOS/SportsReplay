#!/usr/bin/env python3
import time
import Shared.Camera as Camera
import numpy as np
import SharedArray as sa
import multiprocessing as mp
import uuid


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

        self.id = "shm://camera_{camera}_" \
                  "{name_prefix}" \
                  "{camera_time}_" \
                  "{frame_number}_" \
                  "{random}".format(camera=camera.id,
                                    name_prefix=name_prefix,
                                    frame_number=frame_number,
                                    camera_time=int(time.mktime(camera_time) * 10000000000),
                                    random=time.time())
        self.channels = channels
        self.size = size


class SharedCapturedFrameHandler(object):
    @staticmethod
    def get_frame(shared_captured_frame: SharedCapturedFrame) -> (bool, CapturedFrame):
        try:
            if shared_captured_frame is not None:
                frame = sa.attach(shared_captured_frame.id)
                captured_frame: CapturedFrame = CapturedFrame(shared_captured_frame.camera,
                                                              shared_captured_frame.frame_number,
                                                              shared_captured_frame.snapshot_time,
                                                              frame.copy(),
                                                              shared_captured_frame.camera_time)
                SharedCapturedFrameHandler.release(shared_captured_frame)
                return captured_frame
            else:
                return False, None
        except Exception as ex:
            pass
        finally:
            pass
        return False, None

    @staticmethod
    def release(shared_captured_frame: SharedCapturedFrame):
        try:
            if shared_captured_frame is not None:
                sa.delete(shared_captured_frame.id)
        except Exception as ex:
            pass
        finally:
            pass
        return False, None

    @staticmethod
    def get_shared_frame(captured_frame: CapturedFrame, name_prefix) -> SharedCapturedFrame:
        try:
            if captured_frame is not None:
                shared_captured_frame: SharedCapturedFrame = SharedCapturedFrame(captured_frame.camera,
                                                                                 captured_frame.frame_number,
                                                                                 captured_frame.snapshot_time,
                                                                                 captured_frame.camera_time,
                                                                                 name_prefix,
                                                                                 captured_frame.frame.shape[:2],
                                                                                 captured_frame.frame.shape[2])

                shared_array = sa.create(shared_captured_frame.id,
                                         captured_frame.frame.shape,
                                         captured_frame.frame.dtype)
                np.copyto(shared_array, captured_frame.frame)
                return shared_captured_frame
            else:
                return None
        except Exception as ex:
            raise ex
        finally:
            pass

    @staticmethod
    def empty_queue(queue: mp.Queue):
        while queue.qsize() > 0:
            try:
                shared_captured_frame: SharedCapturedFrame = queue.get()
                if shared_captured_frame is not None:
                    SharedCapturedFrameHandler.release(shared_captured_frame)
            except:
                pass

