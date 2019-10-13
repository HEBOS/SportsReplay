#!/usr/bin/env python3
import argparse
import time
import requests
import json
import os
from typing import List
from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions
from Shared.Tv import Tv
from Shared.HttpService import HttpService
from Shared.TvState import TvState
from Shared.TvEventType import TvEventType
from Shared.Match import Match
from omxplayer.player import OMXPlayer
import omxplayer.keys as actionKeys
from pathlib import Path


class TvPlayer(object):
    def __init__(self):
        self.playing: TvState = TvState.IDLE

        config = Configuration()
        self.tv_id = config.tv_box["tv-id"]
        self.playground = config.common["playground"]

        self.heart_beat_post_url = config.api["base-url"] + config.api["tv-heartbeat"]
        self.upload_url = config.api["base-url"] + config.api["movie-upload-url"]
        self.tv_state_url = config.api["base-url"] + config.api["tv-state-url"].replace("{}", self.tv_id)
        self.mark_event_as_consumed_url = config.api["base-url"] + config.api["mark-event-as-consumed-url"]
        self.matches_for_deletion_url = config.api["base-url"] + config.api["matches-for-deletion-url"]\
            .replace("{}", self.playground)
        self.delete_matches_url = config.api["base-url"] + config.api["delete-matches-url"]

        self.intermezzo_path = os.path.join(os.getcwd(), config.tv_box["intermezzo"])
        self.ftp_video_path = config.tv_box["ftp-video-path"]
        self.player_args = config.tv_box["player-args"]

        self.player: OMXPlayer = OMXPlayer(Path(self.intermezzo_path))
        self.currentMatchId: int = 0

    def start(self, debugging: bool):
        self.play_intermezzo()

        while True:
            time.sleep(1)

            # Send heart beat to server every 5 seconds
            if int(time.time()) % 5 == 0:
                # Send heart beats, so that our service is aware that tv player is active
                self.send_heart_beat()

                # Get tv state and activate different player state accordingly
                self.handle_player_events()

                # Get all matches marked for deletion
                self.matches_cleanup()

    def handle_player_events(self):
        state = self.get_tv_state()
        if state is None or state.eventType is None:
            self.play_intermezzo()
        else:
            if state.eventType == TvEventType.STOP:
                if state.currentMatchId == self.currentMatchId:
                    self.currentMatchId = 0
                    self.play_intermezzo()
                self.mark_even_as_consumed(TvEventType(state.eventType))
            elif state.eventType == TvEventType.PAUSE:
                if state.currentMatchId == self.currentMatchId:
                    self.pause()
                self.mark_even_as_consumed(TvEventType(state.eventType))
            elif state.eventType == TvEventType.PLAY:
                self.currentMatchId = state.currentMatchId
                self.play_recording(
                    SharedFunctions.get_output_video(self.ftp_video_path,
                                                     state.playgroundId,
                                                     SharedFunctions.from_post_time(state.currentMatchStartTime)))
                self.mark_even_as_consumed(TvEventType(state.eventType))
            elif state.eventType == TvEventType.FAST_FORWARD:
                if state.currentMatchId == self.currentMatchId:
                    self.fast_forward()
                self.mark_even_as_consumed(TvEventType(state.eventType))
            elif state.eventType == TvEventType.REWIND:
                if state.currentMatchId == self.currentMatchId:
                    self.rewind()
                self.mark_even_as_consumed(TvEventType(state.eventType))
            else:
                self.currentMatchId = 0
                self.play_intermezzo()

    def matches_cleanup(self):
        matches: List[Match] = self.get_matches_for_cleanup()
        for match in matches:
            video_file = SharedFunctions.get_output_video(self.ftp_video_path,
                                                          match.playgroundId,
                                                          SharedFunctions.from_post_time(match.plannedStartTime))
            control_file = video_file.replace(".mp4", ".ready")
            if os.path.isfile(video_file):
                os.remove(video_file)
            if os.path.isfile(control_file):
                os.remove(control_file)
        self.delete_matches_on_server(matches)

    def get_matches_for_cleanup(self) -> List[Match]:
        try:
            response = requests.get(url=self.matches_for_deletion_url)
            if response is None:
                return []

            matches: List[Match] = []
            dict_list = json.loads(response.text)
            for item in dict_list:
                matches.append(Match.parse(item))

            return matches
        except:
            pass

    def delete_matches_on_server(self, matches: List[Match]):
        try:
            requests.delete(url=self.delete_matches_url, data=SharedFunctions.to_post_body(matches))
        except:
            pass

    def play_intermezzo(self):
        video_path = Path(self.intermezzo_path)
        if self.player is not None and self.is_player_alive():
            if self.playing == TvState.INTERMEZZO:
                # Restart, if we are at the end of the video (duration of intermezzo is 60 seconds, which is 60 * 10^6)
                if self.player.position() > 10000000:
                    self.player.set_position(0)
            else:
                self.restart_intermezzo(video_path)
        else:
            self.restart_intermezzo(video_path)

    def restart_intermezzo(self, video_path: str):
        if not self.is_player_alive():
            self.player = OMXPlayer(video_path, args=self.player_args)
            self.player.play()
        else:
            self.player.set_position(0)
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

    def mark_even_as_consumed(self, event_consumed: TvEventType):
        try:
            HttpService.post(url=self.mark_event_as_consumed_url,
                             data=SharedFunctions.to_post_body(
                                 {
                                     'tvId': self.tv_id,
                                     'matchId': self.currentMatchId,
                                     'tvEventType': event_consumed
                                 }
                             ))
        except:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sports Replay TV Handler",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog="Please run using: python3 TvHandler.py --debug true")

    parser.add_argument("--debug", type=int, default=0, help="True for debugging.")
    opt, argv = parser.parse_known_args()
    TvPlayer().start(opt.debug == 1)
