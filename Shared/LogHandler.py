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


class LogHandler(object):
    def __init__(self, application: str, booked_start_time: time):
        config = Configuration()
        self.post_url = config.api["base-url"] + config.api["log"]
        self.client = config.common["client"]
        self.building = config.common["building"]
        self.playground = config.common["playground"]
        self.booked_start_time = booked_start_time
        self.post_queue = queue.Queue()
        self.force_post_complete = False
        self.posting = True
        self.postman = threading.Thread(target=self.post)
        self.postman.start()

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
        self.logger.error(formatted_message)
        self.post_queue.put((time.time(), formatted_message))

    def info(self, message):
        formatted_message = LogHandler.format_message(message)
        self.logger.info(formatted_message)
        self.post_queue.put((time.time(), formatted_message))

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

                if self.post_queue.qsize() > 0:
                    messages = []
                    while self.post_queue.qsize() > 0:
                        messages.append(self.post_queue.get())
                    data = {'client': self.client,
                            'building': self.building,
                            'playground': self.playground,
                            'timestamp': self.booked_start_time,
                            'messages': messages}
                    #requests.post(url=self.post_url, information=data)

