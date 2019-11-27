#!/usr/bin/env python3
import os
import time
import datetime
import ntpath
from multiprocessing import connection
import sys
from dateutil.parser import parse as dateParser
from Shared.Point import Point
from typing import List
import jsonpickle


class SharedFunctions(object):
    VIDEO_EXTENSION: str = "mp4v"
    @staticmethod
    def get_recording_path(root_path: str, playground: int, planned_start_time: float):
        return os.path\
            .normpath(r"{path}/{playground}-{timestamp}"
                      .format(path=root_path,
                              playground=str(playground),
                              timestamp=time.strftime("%Y-%m-%d-%H-%M", time.gmtime(planned_start_time))))

    @staticmethod
    def get_recording_time(start_of_capture: float, camera_timestamp: int) -> time:
        camera_time: float = camera_timestamp / 1000
        return time.localtime(start_of_capture + camera_time)

    @staticmethod
    def get_output_video(root_path: str, playground: int, planned_start_time: float):
        return os.path\
            .normpath(r"{path}/{playground}-{timestamp}.{extension}"
                      .format(path=root_path,
                              playground=str(playground),
                              timestamp=time.strftime("%Y-%m-%d-%H-%M", time.gmtime(planned_start_time)),
                              extension=SharedFunctions.VIDEO_EXTENSION))

    @staticmethod
    def get_json_file_path(file_path: str):
        return file_path.replace(".jpg", ".json")

    @staticmethod
    def ensure_directory_exists(directory: str):
        if not os.path.isdir(directory):
            os.mkdir(directory)

    @staticmethod
    def create_text_file(file_path: str, content: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            f.close()

    @staticmethod
    def read_text_file(file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def create_flag_file(root_path: str):
        ready_flag_file = os.path.normpath("{}/READY.TXT").format(root_path)
        SharedFunctions.create_text_file(ready_flag_file, "")

    @staticmethod
    def create_list_file(file_path: str, lines: List[str]):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(map(lambda s: s + '\n', lines))
            f.close()

    @staticmethod
    def remove_flag_file(root_path: str):
        ready_flag_file = os.path.normpath("{}/READY.TXT").format(root_path)
        os.remove(ready_flag_file)

    @staticmethod
    def get_file_name_only(file_path: str) -> str:
        return ntpath.basename(file_path).replace(".jpg", "").replace(".json", "")

    @staticmethod
    def get_time_from_file(file_path: str) -> str:
        return SharedFunctions.get_file_name_only(file_path).replace("frame_", "").replace("_", ".")

    @staticmethod
    def get_class_id(class_names_file_path: str, target_class_name) -> int:
        return open(class_names_file_path).read().strip().split("\n").index(target_class_name)

    @staticmethod
    def normalise_time(frame_number: int, fps: int) -> str:
        total_seconds = int(frame_number / fps)
        hours = int(total_seconds / 3600)
        minutes = int(int(total_seconds - (hours * 3600)) / 60)
        seconds = total_seconds - (hours * 3600) - (minutes * 60)

        return "{}:{}:{}".format(str(int(hours)).zfill(2),
                                 str(minutes).zfill(2),
                                 str(seconds).zfill(2))

    @staticmethod
    def get_points_array(points: List[Point], ratio=1):
        contours: List[List[int]] = []
        for p in points:
            contours.append([int(p.x * ratio), int(p.y * ratio)])
        return contours

    @staticmethod
    def planned_start_time(hour: int, minute: int):
        today = datetime.datetime.now()
        planned_start_time = datetime.datetime(today.year, today.month, today.day, hour, minute, 0, 0)
        return time.mktime(planned_start_time.timetuple()) + planned_start_time.microsecond / 1E6

    @staticmethod
    def is_number(s) -> bool:
        try:
            float(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def get_exception_info(ex) -> str:
        inst = "Exeption type: {}".format(type(ex))

        exc_type, exc_obj, exc_tb = sys.exc_info()
        file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        return "{}, line {}, {}, {}".format(file_name, exc_tb.tb_lineno, ex, inst)

    @staticmethod
    def get_time_zone_offset():
        ts = time.time()
        utc_offset = (datetime.datetime.fromtimestamp(ts) -
                      datetime.datetime.utcfromtimestamp(ts)).total_seconds()
        return utc_offset

    @staticmethod
    def to_post_time(value: time) -> str:
        if value is None:
            return None
        formatted_date = datetime.datetime.utcfromtimestamp(value).isoformat()
        return formatted_date[:-3]

    @staticmethod
    def from_post_time(value: str) -> time:
        if value is None:
            return None
        date = dateParser(value)
        return time.mktime(date.timetuple()) + date.microsecond / 1E6 + SharedFunctions.get_time_zone_offset()

    @staticmethod
    def to_post_body(data) -> str:
        return jsonpickle.encode(data)

    @staticmethod
    def close_connection(conn: connection.Connection):
        try:
            conn.close()
        except:
            pass
