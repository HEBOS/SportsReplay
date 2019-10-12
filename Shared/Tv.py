#!/usr/bin/env python3
from typing import Optional


class Tv(object):
    def __init__(self):
        self.id: Optional[int] = None
        self.number: Optional[int] = None
        self.clientId: Optional[int] = None
        self.playgroundId: Optional[int] = None
        self.currentMatchId: Optional[int] = None
        self.playgroundNumber: Optional[int] = None
        self.eventType: Optional[int] = None
        self.currentMatchStartTime: Optional[int] = None
        self.currentMatchEndTime: Optional[int] = None
        self.lastActivityTime: Optional[int] = None

    @staticmethod
    def parse(json: dict):
        tv = Tv()
        tv.id = json["id"]
        tv.number = json["number"]
        tv.clientId = json["clientId"]
        tv.playgroundId = json["playgroundId"]
        tv.currentMatchId = json["currentMatchId"]
        tv.playgroundNumber = json["playgroundNumber"]
        tv.eventType = json["eventType"]
        tv.currentMatchStartTime = json["currentMatchStartTime"]
        tv.currentMatchEndTime = json["currentMatchEndTime"]
        tv.lastActivityTime = json["lastActivityTime"]
        return tv
