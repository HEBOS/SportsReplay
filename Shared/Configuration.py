#!/usr/bin/env python
import configparser
import os
import platform


class Configuration(object):
    def __init__(self):
        # location = "/etc/sports-replay"
        location = "Shared/sports-replay.ini"
        self.recorder = {}
        self.activity_detector = {}
        self.logger = {}
        self.post_recorder = {}
        self.video_maker = {}
        self.common = {}

        # for debugging purposes only
        if platform.system() == "Windows":
            location = os.path.normpath(r"/SportsReplay/Shared/sports-replay.ini")

        if not os.path.isfile(location):
            raise "File is not found {}".format(location)

        config = configparser.ConfigParser()
        config.read(location)

        for section in config.sections():
            for option in config.options(section):
                if section == "recorder":
                    self.recorder[option] = config.get(section, option)
                if section == "post-recorder":
                    self.post_recorder[option] = config.get(section, option)
                if section == "activity-detector":
                    self.activity_detector[option] = config.get(section, option)
                if section == "video-maker":
                    self.video_maker[option] = config.get(section, option)
                if section == "logger":
                    self.logger[option] = config.get(section, option)
                if section == "common":
                    self.common[option] = config.get(section, option)
