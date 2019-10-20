#!/usr/bin/env python3
from enum import Enum


class TvEventType(Enum):
    NONE = "NONE"
    PLAY = "PLAY"
    STOP = "STOP"
    PAUSE = "PAUSE"
    FAST_FORWARD = "FAST_FORWARD"
    REWIND = "REWIND"
