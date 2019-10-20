#!/usr/bin/env python3
from Shared.TvEventType import TvEventType


class TvEvent(object):
    def __init__(self):
        self.id: int = int()
        self.tvId: int = int()
        self.playgroundId: int = int()
        self.matchId: int = int()
        self.plannedStartTime: str = str()
        self.eventType: TvEventType = TvEventType.NONE
        self.timestamp: str = str()

    @staticmethod
    def parse(json: dict):
        tv_event = TvEvent()
        tv_event.id = json["id"]
        tv_event.tvId = json["tvId"]
        tv_event.playgroundId = json["playgroundId"]
        tv_event.matchId = json["matchId"]
        tv_event.plannedStartTime = json["plannedStartTime"]
        tv_event.timestamp = json["timestamp"]

        try:
            tv_event.eventType = TvEventType(json["eventType"])
        except:
            tv_event.eventType = TvEventType[json["eventType"]]

        return tv_event
