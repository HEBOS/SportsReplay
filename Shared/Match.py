#!/usr/bin/env python3
from typing import Optional


class Match(object):
    def __init__(self):
        self.id: Optional[int] = None
        self.playgroundId: Optional[int] = None
        self.plannedStartTime: Optional[int] = None

    @staticmethod
    def parse(json: dict):
        match = Match()
        match.id = json["id"]
        match.playgroundId = json["playgroundId"]
        match.plannedStartTime = json["plannedStartTime"]
        return match
