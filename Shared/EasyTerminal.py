#!/usr/bin/env python3
import os


class EasyTerminal(object):
    def print(self, message: str, padding: int):
        print(message.ljust(padding))
