#!/usr/bin/env python3
import os
import time
import ntpath
import cv2
from typing import List
from Shared.Detection import Detection

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
    def get_recording_file_path(path: str, current_time: int, frame_number: int):
        return os.path.normpath(
            r"{target_path}/frame_{currentTime}_{frameNumber}.jpg".format(
                target_path=path,
                currentTime=current_time,
                frameNumber=str(frame_number).zfill(4)
            ))

    @staticmethod
    def get_recording_file_name(current_time: int, frame_number: int):
        return os.path.normpath(
            r"frame_{currentTime}_{frameNumber}.jpg".format(
                currentTime=current_time,
                frameNumber=str(frame_number).zfill(4)
            ))

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

    # The reference for these methods: https://gist.github.com/atinfinity/b2f89e33e398559c5fcefda3ad3c0269
    @staticmethod
    def from_cuda(image: cv2.cuda_GpuMat):
        return image.download()

    @staticmethod
    def to_cuda(image) -> cv2.cuda_GpuMat:
        d_img = cv2.cuda_GpuMat()
        d_img.upload(image)

