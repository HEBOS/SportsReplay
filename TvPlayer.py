#!/usr/bin/env python3
import threading
import argparse
import time
import requests
import json
import os
from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions
from Shared.Tv import Tv
from Shared.HttpService import HttpService
from Shared.TvState import  TvState
from Shared.TvEventType import TvEventType
from omxplayer.player import OMXPlayer
import omxplayer.keys as actionKeys
from pathlib import Path


class TvPlayer(object):
    def __init__(self):
        self.playing: TvState = TvState.IDLE

        config = Configuration()
        self.tv_id = config.tv_box["tv-id"]

        self.heart_beat_post_url = config.api["base-url"] + config.api["tv-heartbeat"]
        self.upload_url = config.api["base-url"] + config.api["movie-upload-url"]
        self.tv_state_url = config.api["base-url"] + config.api["tv-state-url"].replace("{}", self.tv_id)
        self.intermezzo_path = os.path.join(os.getcwd(), config.tv_box["intermezzo"])
        self.ftp_video_path = config.tv_box["ftp-video-path"]
        self.player_args = config.tv_box["player-args"]

        self.player: OMXPlayer = OMXPlayer(Path(self.intermezzo_path))

    def start(self, debugging: bool):
        self.play_intermezzo()

        while True:
            time.sleep(1)

            # Send heart beat to server every 5 seconds
            if int(time.time()) % 5 == 0:
                self.send_heart_beat()
                state = self.get_tv_state()
                if state is None or state.eventType is None:
                    self.play_intermezzo()
                else:
                    if state.eventType == TvEventType.STOP:
                        self.play_intermezzo()
                    elif state.eventType == TvEventType.PAUSE:
                        self.pause()
                    elif state.eventType == TvEventType.PLAY:
                        self.play_recording(
                            SharedFunctions.get_output_video(self.ftp_video_path,
                                                             state.playgroundId,
                                                             state.currentMatchStartTime))
                    elif state.eventType == TvEventType.FAST_FORWARD:
                        self.fast_forward()
                    elif state.eventType == TvEventType.REWIND:
                        self.rewind()
                    else:
                        self.play_intermezzo()

    def play_intermezzo(self):
        video_path = Path(self.intermezzo_path)
        if self.player is not None and self.is_player_alive():
            if not self.playing == TvState.INTERMEZZO:
                self.player.stop()
                self.player = OMXPlayer(video_path, args=self.player_args)
                self.player.play()
                time.sleep(2)
                self.pause()
        else:
            self.player = OMXPlayer(video_path, args=self.player_args)
            self.player.play()
            time.sleep(2)
            self.pause()

        self.playing = TvState.INTERMEZZO

    def play_recording(self, recording_path: str):
        video_path = Path(recording_path)
        print("")
        print("Playing video {}".format(video_path))

        if self.player is not None and self.is_player_alive():
            self.player.stop()

        self.player = OMXPlayer(video_path, args=self.player_args)
        self.player.play()
        self.playing = TvState.PLAYING

    def fast_forward(self):
        if self.player is not None and self.is_player_alive():
            self.player.action(actionKeys.FAST_FORWARD)

    def rewind(self):
        if self.player is not None and self.is_player_alive():
            self.player.action(actionKeys.REWIND)

    def pause(self):
        if self.player is not None and self.is_player_alive():
            self.player.action(actionKeys.PAUSE)

    def get_tv_state(self) -> Tv:
        try:
            response = requests.get(url=self.tv_state_url)
            if response is not None:
                print("")
                print(response.text)
            if response is None:
                return Tv()
            return Tv.parse(json.loads(response.text))
        except:
            pass

    def send_heart_beat(self):
        try:
            HttpService.post(url=self.heart_beat_post_url,
                             data=SharedFunctions.to_post_body(
                                 {'id': self.tv_id}
                             ))
        except:
            pass

    def is_player_alive(self):
        try:
            self.player.is_playing()
            return True
        except:
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sports Replay TV Handler",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog="Please run using: python3 TvHandler.py --debug true")

    parser.add_argument("--debug", type=int, default=0, help="True for debugging.")
    opt, argv = parser.parse_known_args()
    TvPlayer().start(opt.debug == 1)
