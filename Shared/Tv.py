#!/usr/bin/env python3
from Shared.TvEventType import TvEventType


class Tv(object):
    def __init__(self):
        self.id: int = int()
        self.number: int = int()
        self.clientId: int = int()
        self.playgroundId: int = int()
        self.currentMatchId: int = int()
        self.playgroundNumber: int = int()
        self.eventType: TvEventType = TvEventType.NONE
        self.currentMatchStartTime: str = str()
        self.currentMatchEndTime: str = str()
        self.lastActivityTime: str = str()

    @staticmethod
    def parse(json: dict):
        tv = Tv()
        tv.id = json["id"]
        tv.number = json["number"]
        tv.clientId = json["clientId"]
        tv.playgroundId = json["playgroundId"]
        tv.currentMatchId = json["currentMatchId"]
        tv.playgroundNumber = json["playgroundNumber"]

        try:
            tv.eventType = TvEventType(json["eventType"])
        except:
            tv.eventType = TvEventType[json["eventType"]]

        tv.currentMatchStartTime = json["currentMatchStartTime"]
        tv.currentMatchEndTime = json["currentMatchEndTime"]
        tv.lastActivityTime = json["lastActivityTime"]
        return tv
