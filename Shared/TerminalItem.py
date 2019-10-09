#!/usr/bin/env python3
from Shared.EasyTerminal import EasyTerminal
from Shared.SharedFunctions import SharedFunctions


class TerminalItem(object):
    def __init__(self, terminal: EasyTerminal, label_type: int, caption: str, padding: int):
        self.terminal = terminal
        self.label_type = label_type
        self._value = ""
        self.padding = padding
        self.caption = caption

    def set_value(self, value):
        self._value = value
        self.refresh()

    def increment_value(self, value):
        if self._value == "":
            self._value = 0

        if SharedFunctions.is_number(self._value):
            self._value = int(self._value) + int(value)
            self.refresh()
        else:
            raise "Cannot add value " + value

    def refresh(self):
        self.terminal.print(self.caption + str(self._value), self.padding + len(self.caption))
