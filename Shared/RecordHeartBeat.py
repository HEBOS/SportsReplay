import time
from Shared.SharedFunctions import SharedFunctions


class RecordHeartBeat(object):
    _video_recorder_1: time
    _video_recorder_2: time
    _video_maker: time
    _detector: time

    def __init__(self, playground: int, planned_start_time: time):
        self._playground = playground
        self._planned_start_time = planned_start_time

    def set_video_maker(self, value: time):
        self._video_maker = value

    def set_video_recorder_1(self, value: time):
        self._video_recorder_1 = value

    def set_video_recorder_2(self, value: time):
        self._video_recorder_2 = value

    def set_detector(self, value: time):
        self._detector = value

    def to_post_body(self):
        return {'playgroundId': self._playground,
                'plannedStartTime': SharedFunctions.to_post_time(self._planned_start_time),
                'camera1Activity': SharedFunctions.to_post_time(self._video_recorder_1),
                'camera2Activity': SharedFunctions.to_post_time(self._video_recorder_2),
                'videoMakerActivity': SharedFunctions.to_post_time(self._video_maker),
                'detectorActivity': SharedFunctions.to_post_time(self._detector)}
