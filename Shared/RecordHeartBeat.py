import time
import json
from Shared.SharedFunctions import SharedFunctions


class RecordHeartBeat(object):
    def __init__(self, playground: int, planned_start_time: time, planned_end_time: time):
        self.playground = playground
        self.planned_start_time = planned_start_time
        self.planned_end_time = planned_end_time
        self._video_recorder_1: time = None
        self._video_recorder_2: time = None
        self._video_maker: time = None
        self._detector: time = None
        self._actual_start_time: time = None
        self._actual_end_time: time = None
        self._completed: bool = False

    def set_video_maker(self, value: time):
        self._video_maker = value

    def set_video_recorder_1(self, value: time):
        self._video_recorder_1 = value

    def set_video_recorder_2(self, value: time):
        self._video_recorder_2 = value

    def set_detector(self, value: time):
        self._detector = value

    def set_actual_start_time(self, value: time):
        # Set it only once
        if self._actual_start_time is None:
            self._actual_start_time = value

    def set_actual_end_time(self, value: time):
        self._actual_end_time = value

    def set_completed(self):
        self._completed = True

    def to_post_body(self):
        data = {'playgroundId': self.playground,
                'plannedStartTime': SharedFunctions.to_post_time(self.planned_start_time),
                'plannedEndTime': SharedFunctions.to_post_time(self.planned_end_time),
                'actualStartTime': SharedFunctions.to_post_time(self._actual_start_time),
                'actualEndTime': SharedFunctions.to_post_time(self._actual_end_time),
                'completed': self._completed,
                'camera1Activity': SharedFunctions.to_post_time(self._video_recorder_1),
                'camera2Activity': SharedFunctions.to_post_time(self._video_recorder_2),
                'videoMakerActivity': SharedFunctions.to_post_time(self._video_maker),
                'detectorActivity': SharedFunctions.to_post_time(self._detector),
                }
        return json.dumps(data)
