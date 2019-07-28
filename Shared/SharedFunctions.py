import os
import time


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
    def get_previous_frame_file_name(path: str, camera_number: int, current_time: int, frame_number: int, fps: int):
        if frame_number == 1:
            seconds = int(current_time) - 1
            frame = fps + 1
        else:
            seconds = int(current_time)
            frame = frame_number - 1

        return SharedFunctions.get_recording_file_path(path, camera_number, seconds, frame)

    @staticmethod
    def get_next_frame_file_name(path: str, camera_number: int, current_time: int, frame_number: int, fps: int):
        if frame_number == fps + 1:
            seconds = int(current_time) + 1
            frame = 1
        else:
            seconds = int(current_time)
            frame = frame_number + 1

        return SharedFunctions.get_recording_file_path(path, camera_number, seconds, frame)

    @staticmethod
    def get_recording_file_path(path: str, camera_number: int, current_time: int, frame_number: int):
        return os.path.normpath(
            r"{target_path}/camera_{camera_number}_frame_{currentTime}_{frameNumber}.jpg".format(
                target_path=path,
                camera_number=camera_number,
                currentTime=current_time,
                frameNumber=str(frame_number).zfill(4)
            ))

    @staticmethod
    def get_recording_file_name(camera_number: int, current_time: int, frame_number: int):
        return os.path.normpath(
            r"camera_{camera_number}_frame_{currentTime}_{frameNumber}.jpg".format(
                camera_number=camera_number,
                currentTime=current_time,
                frameNumber=str(frame_number).zfill(4)
            ))

    @staticmethod
    def get_json_file_path(file_path: str):
        return file_path.replace(".jpg", ".json")
