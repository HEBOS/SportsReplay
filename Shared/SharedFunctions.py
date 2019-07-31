import os
import time
import shutil
import ntpath

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
    def remove_flag_file(root_path: str):
        ready_flag_file = os.path.normpath("{}/READY.TXT").format(root_path)
        os.remove(ready_flag_file)

    @staticmethod
    def get_file_name_only(file_path: str) -> str:
        return ntpath.basename(file_path).replace(".jpg", "").replace(".json", "")

    @staticmethod
    def get_time_from_file(file_path: str) -> str:
        return SharedFunctions.get_file_name_only(file_path).replace("frame_", "")

