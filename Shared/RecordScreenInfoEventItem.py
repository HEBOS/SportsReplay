#!/usr/bin/env python3
class RecordScreenInfoEventItem(object):
    def __init__(self, info_type: int, operation: int, value: object):
        self.type: int = info_type
        self.operation: int = operation
        self.value = value
