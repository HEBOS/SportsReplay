#!/usr/bin/env python3
import time
from Shared.SharedFunctions import SharedFunctions


class Match(object):
    def __init__(self):
        self.id: int = int()
        self.playgroundId: int = int()
        self.plannedStartTime: str = str()

    @staticmethod
    def parse(json: dict):
        match = Match()
        match.id = json["id"]
        match.playgroundId = json["playgroundId"]
        match.plannedStartTime = json["plannedStartTime"]
        return match
