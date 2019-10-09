#!/usr/bin/env python3
import threading
import argparse
import keyboard
import time
import requests
import json
from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions
from Shared.RecordHeartBeat import RecordHeartBeat
from Shared.HttpService import HttpService

class TvBox(object):
    def __init__(self):
        self.playing = True
        self.dispatch_lock = threading.Lock()

        config = Configuration()
        self.tv_id = config.tv_box["tv-id"]

        self.heart_beat_post_url = config.api["base-url"] + config.api["tv-heartbeat"]
        self.upload_url = config.api["base-url"] + config.api["movie-upload-url"]
        self.tv_state_url = "{}/{}".format(config.api["tv-state-url"], self.tv_id)

    def start(self, debugging: bool):
        while True:
            time.sleep(1)
            if keyboard.is_pressed(27):
                break

            # Send heart beat to server every 5 seconds
            if int(time.time()) % 5 == 0:
                self.send_heart_beat()

            # Get next event type
            request


    def get_tv_state(self) -> OVDJE STAVITI TIP OBJEKTA, I INAČE UVESTI SVE OBJEKTE IZ JAVA PROGRAMA, RELEVANTNE ZA PYTHON:
        try:
            tv_state = requests.get(url=self.tv_state_url)
        except:
            pass

    def send_heart_beat(self):
        try:
            data = json.dumps({'last_activity': SharedFunctions.to_post_time(time.time())})
            HttpService.post(url=self.heart_beat_post_url,
                             data=data)
        except:
            pass


    def play(self):
        outgoing_pipeline = "filesrc location={location} " \
                            "! qtdemux " \
                            "! queue " \
                            "! h264parse " \
                            "! omxh264dec " \
                            "! video/x-raw,format=NV12,width=1280,height=720,framerate=25/1 " \
                            "! videoconvert " \
                            "! nvoverlaysink -e".format(location=location,
                                                        fps=fps,
                                                        width=width,
                                                        height=height)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sports Replay TV Handler",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog="Please run using: python3 TvHandler.py --debug true")

    parser.add_argument("--debug", type=int, default=0, help="True for debugging.")
    opt, argv = parser.parse_known_args()
    Play().start(opt.debug == 1)
