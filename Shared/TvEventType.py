#!/usr/bin/env python3
from enum import Enum


class TvEventType(Enum):
    NONE = 0
    PLAY = 1
    STOP = 2
    PAUSE = 3
    FAST_FORWARD = 4
    REWIND = 5


