#!/usr/bin/env python3
import os
import time
import ntpath
import cv2
from typing import List


class SharedFunctions(object):
    @staticmethod
    def get_recording_path(root_path: str, building: int, playground: int, current_time: float):
        return os.path\
            .normpath(r"{path}/{building}-{playground}-{timestamp}"
                      .format(path=root_path,
                              building=str(building).zfill(5),
                              playground=str(playground).zfill(3),
                              timestamp=time.strftime("%Y-%m-%d-%H-%M", time.localtime(current_time))))

    @staticmethod
    def get_output_video(root_path: str, building: int, playground: int, current_time: float):
        return os.path\
            .normpath(r"{path}/{building}-{playground}-{timestamp}.mp4v"
                      .format(path=root_path,
                              building=str(building).zfill(5),
                              playground=str(playground).zfill(3),
                              timestamp=time.strftime("%Y-%m-%d-%H-%M", time.localtime(current_time))))

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
    def release_open_cv():
        cv2.waitKey(1)
        cv2.destroyAllWindows()
        for i in range(1, 5):
            cv2.waitKey(1)


