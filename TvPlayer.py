#!/usr/bin/env python3
import argparse
import time
import requests
import jsonpickle
import os
import sys
import threading
from typing import List
import atexit
from omxplayer.player import OMXPlayer
import omxplayer.keys as actionKeys
from pathlib import Path
from Shared.Configuration import Configuration
from Shared.SharedFunctions import SharedFunctions
from Shared.TvEvent import TvEvent
from Shared.HttpService import HttpService
from Shared.TvState import TvState
from Shared.TvEventType import TvEventType
from Shared.Match import Match


class TvPlayer(object):
    def __init__(self):
        atexit.register(self.exit_handler)
        self.debugging = False
        self._playing: TvState = TvState.IDLE
        self.playing_lock = threading.Lock()
        self.previous_event: TvEventType = TvEventType.NONE

        config = Configuration()
        self.tv_id = config.tv_box["tv-id"]
        self.playground = config.common["playground"]

        self.heart_beat_post_url = config.api["base-url"] + config.api["tv-heartbeat"]
        self.upload_url = config.api["base-url"] + config.api["movie-upload-url"]
        self.tv_state_url = config.api["base-url"] + config.api["tv-state-url"]
        self.mark_event_as_consumed_url = config.api["base-url"] + config.api["mark-event-as-consumed-url"]
        self.matches_for_deletion_url = config.api["base-url"] + config.api["matches-for-deletion-url"]
        self.delete_matches_url = config.api["base-url"] + config.api["delete-matches-url"]

        self.intermezzo_path = os.path.join(os.getcwd(), config.tv_box["intermezzo"])
        self.ftp_video_path = config.tv_box["ftp-video-path"]
        self.player_args = config.tv_box["player-args"]

        self.player: OMXPlayer = None
        self.create_player(self.intermezzo_path)

        self.currentMatchId: int = 0
        self.played_video = ""

        self.cleanup_thread_lock = threading.Lock()
        self.cleanup_thread_active = True
        self.cleanup_thread = threading.Thread(target=self.matches_cleanup)
        self.cleanup_thread.start()

    def start(self, debugging: bool):
        self.debugging = debugging
        self.disable_terminal()
        self.play_intermezzo()

        last_call = time.time()
        while True:
            try:
                # Send heart beat to server every 5 seconds
                if time.time() - last_call > 0.2:
                    last_call = time.time()
                    # Send heart beats, so that our service is aware that tv player is active
                    #self.send_heart_beat()

                    # Get tv state and activate different player state accordingly
                    self.handle_player_events()

                    print("")
                    print("Playground: {}".format(self.playground))
                    if self.currentMatchId > 0:
                        print("Most recent active match: {}".format(self.currentMatchId))

                    print("")
                    print("Executing action: {}".format(self.get_playing().name))
                    if self.get_playing() == TvState.PLAYING:
                        print("Playing video: {}".format(self.played_video))
            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, file_name, exc_tb.tb_lineno)

    def exit_handler(self):
        self.enable_terminal()
        with self.cleanup_thread_lock:
            self.cleanup_thread_active = False
        self.cleanup_thread.join()

    def handle_player_events(self):
        events = self.get_tv_events()
        if events is None or len(events) == 0:
            if self.get_playing() == TvState.INTERMEZZO:
                self.play_intermezzo()
            elif self.get_playing() == TvState.IDLE:
                self.restart_intermezzo()
        else:
            for event in events:
                if event is None or event.eventType is None:
                    self.play_intermezzo()
                else:
                    if event.eventType == TvEventType.STOP:
                        self.quit_player()
                        self.play_intermezzo()
                        self.mark_event_as_consumed(event.id)
                    elif event.eventType == TvEventType.PAUSE:
                        if event.matchId == self.currentMatchId:
                            self.pause()
                        self.mark_event_as_consumed(event.id)
                    elif event.eventType == TvEventType.PLAY:
                        self.currentMatchId = event.matchId
                        self.play_recording(
                            SharedFunctions.get_output_video(self.ftp_video_path,
                                                             event.playgroundId,
                                                             SharedFunctions.from_post_time(event.plannedStartTime)))
                        self.mark_event_as_consumed(event.id)
                    elif event.eventType == TvEventType.FAST_FORWARD:
                        if event.matchId == self.currentMatchId:
                            self.fast_forward()
                        self.mark_event_as_consumed(event.id)
                    elif event.eventType == TvEventType.REWIND:
                        if event.matchId == self.currentMatchId:
                            self.rewind()
                        self.mark_event_as_consumed(event.id)
                    else:
                        self.currentMatchId = 0
                        self.play_intermezzo()
                self.previous_event = event.eventType

    def matches_cleanup(self):
        cleanup_thread_active = True
        while cleanup_thread_active:
            with self.cleanup_thread_lock:
                cleanup_thread_active = self.cleanup_thread_active

            matches: List[Match] = self.get_matches_for_cleanup()
            for match in matches:
                video_file = SharedFunctions.get_output_video(self.ftp_video_path,
                                                              match.playgroundId,
                                                              SharedFunctions.from_post_time(match.plannedStartTime))
                control_file = video_file.replace(".{extension}".format(extension=SharedFunctions.VIDEO_EXTENSION),
                                                  ".{extension}.ready".format(extension=SharedFunctions.VIDEO_EXTENSION))
                if os.path.isfile(video_file):
                    os.remove(video_file)
                if os.path.isfile(control_file):
                    os.remove(control_file)
                self.delete_match_on_server(match.id)
            time.sleep(5)

    def get_matches_for_cleanup(self) -> List[Match]:
        try:
            response = requests.get(url=self.matches_for_deletion_url.replace("{}", str(self.playground)))
            if response is None:
                return []

            matches: List[Match] = []
            dict_list = jsonpickle.decode(response.text)
            for item in dict_list:
                matches.append(Match.parse(item))

            return matches
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, file_name, exc_tb.tb_lineno)
            pass

    def delete_match_on_server(self, matchId: int):
        try:
            requests.delete(url=self.delete_matches_url.replace("{}", str(matchId)))
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, file_name, exc_tb.tb_lineno)
            pass

    def get_intermezzo_path(self):
        return Path(self.intermezzo_path)

    def play_intermezzo(self):
        if self.player is not None and self.is_player_alive():
            if self.get_playing() == TvState.INTERMEZZO:
                # Restart, if we are at the end of the video (duration of intermezzo is 60 seconds, which is 60 * 10^6)
                if self.player.position() > 10:
                    self.player.set_position(0)
            else:
                self.restart_intermezzo()
        else:
            self.restart_intermezzo()

    def restart_intermezzo(self):
        video_path = self.get_intermezzo_path()
        if not self.is_player_alive():
            self.create_player(video_path)
            self.player.play()
        else:
            self.player.set_position(0)
        self.set_playing(TvState.INTERMEZZO)

    def play_recording(self, recording_path: str):
        if (self.previous_event == TvEventType.PLAY or
            self.previous_event == TvEventType.REWIND or
            self.previous_event == TvEventType.FAST_FORWARD or
            self.previous_event == TvEventType.PAUSE) \
                and self.get_playing() == TvState.PLAYING and self.player is not None and self.is_player_alive():
            self.player.play()
            self.player.set_rate(1)
        else:
            if os.path.isfile(recording_path):
                video_path = Path(recording_path)

                if self.player is not None and self.is_player_alive():
                    self.quit_player()

                self.create_player(video_path)
                self.player.play()
                self.player.set_rate(1)
                self.set_playing(TvState.PLAYING)
            else:
                print("File {} is not found. Playing Intermezzo.".format(recording_path))
                self.set_playing(TvState.IDLE)

    def quit_player(self):
        if self.player is not None and self.is_player_alive():
            self.player.stop()
            self.player.quit()

        self.player = None
        self.set_playing(TvState.IDLE)

    def fast_forward(self):
        if self.player is not None and self.is_player_alive():
            position = self.player.position()
            duration = self.player.duration()
            if position + 30 < duration:
                self.player.set_position(position + 30)
            else:
                self.player.set_position(duration - 1)

    def rewind(self):
        if self.player is not None and self.is_player_alive():
            position = self.player.position()
            if position - 10 >= 0:
                self.player.set_position(position - 10)
            else:
                self.player.set_position(0)

    def pause(self):
        if self.player is not None and self.is_player_alive():
            self.player.play_pause()

    def get_tv_events(self) -> List[TvEvent]:
        try:
            response = requests.get(url=self.tv_state_url.replace("{}", str(self.tv_id)))
            if response is not None:
                print("")
                print(response.text)
            if response is None:
                return []

            events: List[TvEvent] = []
            dict_list = jsonpickle.decode(response.text)
            for item in dict_list:
                events.append(TvEvent.parse(item))

            return events
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, file_name, exc_tb.tb_lineno)
            pass

    def send_heart_beat(self):
        try:
            HttpService.post(url=self.heart_beat_post_url,
                             data=SharedFunctions.to_post_body(
                                 {'id': self.tv_id}
                             ))
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, file_name, exc_tb.tb_lineno)
            pass

    def is_player_alive(self):
        try:
            self.player.is_playing()
            return True
        except Exception as ex:
            pass

    def mark_event_as_consumed(self, tvEventId: int):
        try:
            HttpService.post(url=self.mark_event_as_consumed_url,
                             data=SharedFunctions.to_post_body(
                                 {
                                     'id': tvEventId
                                 }
                             ))
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, file_name, exc_tb.tb_lineno)
            pass

    def end_playing(self, exit_code):
        self.quit_player()

    def get_playing(self):
        with self.playing_lock:
            return self._playing

    def set_playing(self, value: TvState):
        with self.playing_lock:
            self._playing = value

    def create_player(self, video_path: str):
        self.quit_player()
        self.player = OMXPlayer(Path(video_path), args=self.player_args)
        self.player.exitEvent += lambda _, exit_code: self.end_playing(exit_code)

    def disable_terminal(self):
        if not self.debugging:
            os.system("printf '\\e[48;5;255m Background color: White\\n'")
            os.system("clear")

    def enable_terminal(self):
        if not self.debugging:
            os.system("printf '\\e[48;5;0m Background color: Black\\n'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sports Replay TV Handler",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog="Please run using: python3 TvHandler.py --debug true")

    parser.add_argument("--debug", type=int, default=0, help="True for debugging.")
    opt, argv = parser.parse_known_args()

    TvPlayer().start(opt.debug == 1)

