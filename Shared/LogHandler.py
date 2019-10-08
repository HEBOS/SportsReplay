#!/usr/bin/env python3
import os
import logging
import requests
import time
import queue
import threading
from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions
from Shared.RecordScreenInfoEventItem import RecordScreenInfoEventItem
from Shared.RecordScreenInfo import RecordScreenInfo
from Shared.RecordHeartBeat import RecordHeartBeat


class LogHandler(object):
    def __init__(self, application: str, planned_start_time: time):
        config = Configuration()
        self.heart_beat_post_url = config.api["base-url"] + config.api["record-heartbeat"]
        self.log_post_url = config.api["base-url"] + config.api["log"]
        self.playground = config.common["playground"]
        self.planned_start_time = planned_start_time
        self.post_queue = queue.Queue()
        self.force_post_complete = False
        self.posting = True
        self.postman = threading.Thread(target=self.post)
        self.postman.start()
        self.heart_beat_lock = threading.Lock()
        self.heart_beat = RecordHeartBeat(self.playground, self.planned_start_time)

        path = os.path.join(config.common["dump-path"], config.common["log-files"])
        SharedFunctions.ensure_directory_exists(path)
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename=os.path.normpath('{}/sports-replay-{}-info.log'.format(path, application)),
                            filemode='w')

        self.logger = logging.getLogger(application)
        error_handler = logging.FileHandler(os.path.normpath('{}/sports-replay-{}-error.log'.format(path, application)))
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)

        info_handler = logging.FileHandler(os.path.normpath('{}/sports-replay-{}-info.log'.format(path, application)))
        info_handler.setLevel(logging.INFO)
        self.logger.addHandler(info_handler)

        warning_handler = logging.FileHandler(
            os.path.normpath('{}/sports-replay-{}-warning.log'.format(path, application)))
        warning_handler.setLevel(logging.WARNING)
        self.logger.addHandler(warning_handler)

    def error(self, message: RecordScreenInfoEventItem):
        formatted_message = LogHandler.format_message(message)
        self.update_heart_beat(message)
        self.logger.error(formatted_message)
        try:
            error_data = {'playgroundId': self.playground,
                          'plannedStartTime': SharedFunctions.to_post_time(self.planned_start_time),
                          'error': message}
            requests.post(url=self.log_post_url, information=error_data)
            pass
        except:
            pass


    def info(self, message: RecordScreenInfoEventItem):
        formatted_message = LogHandler.format_message(message)
        self.update_heart_beat(message)
        self.logger.info(formatted_message)

    def update_heart_beat(self, message: RecordScreenInfoEventItem):
        with self.heart_beat_lock:
            if message.type == RecordScreenInfo.VM_IS_LIVE:
                self.heart_beat.set_video_maker(time.time())
            elif message.type == RecordScreenInfo.VR_HEART_BEAT and int(message.value) == 1:
                self.heart_beat.set_video_recorder_1(time.time())
            elif message.type == RecordScreenInfo.VR_HEART_BEAT and int(message.value) == 2:
                self.heart_beat.set_video_recorder_2(time.time())
            elif message.type == RecordScreenInfo.AI_IS_LIVE:
                self.heart_beat.set_detector(time.time())

    @staticmethod
    def format_message(message: RecordScreenInfoEventItem):
        return "{}: {}".format(RecordScreenInfo.from_enum(message.type), str(message.value))

    def stop_posting(self):
        self.force_post_complete = True
        self.postman.join()

    def post(self):
        last_post = time.time()
        while self.posting:
            if last_post - time.time() >= 5 or self.force_post_complete:
                # This is to force exit, after stop_posting has been requested
                self.posting = False

                with self.heart_beat_lock:
                    try:
                        requests.post(url=self.heart_beat_post_url, information=self.heart_beat.to_post_body())
                        pass
                    except:
                        pass
