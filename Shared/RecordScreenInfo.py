import time
from Shared.TerminalItem import TerminalItem
from Shared.EasyTerminal import EasyTerminal


class RecordScreenInfo(object):
    LIVE_PROCESSES: int = 1
    AI_EXCEPTIONS: int = 2
    AI_IS_LIVE: int = 3
    AI_DETECTIONS_PER_SECOND: int = 4
    AI_QUEUE_COUNT: int = 5
    VR_EXCEPTIONS: int = 6
    VR_RECORDING_START_SCHEDULED: int = 7
    VR_RECORDING_STARTED: int = 8
    VR_RECORDING_END_SCHEDULED: int = 9
    VR_TOTAL_CAMERAS: int = 10
    VR_HEART_BEAT: int = 12
    VR_ACTIVE_CAMERA: int = 13
    VM_EXCEPTIONS: int = 14
    VM_WRITTEN_FRAMES: int = 15
    VM_QUEUE_COUNT: int = 16
    ERROR_LOG: int = 17
    CURRENT_TASK: int = 18
    VM_IS_LIVE: int = 19
    COMPLETED: int = 21

    def __init__(self, terminal: EasyTerminal):
        self.terminal = terminal
        self.terminal_items = [
            TerminalItem(terminal, 0, "AI Detections ", 0),
            TerminalItem(terminal, 0, "-" * 50, 5),
            TerminalItem(terminal, 0, "Video Recorder ", 0),
            TerminalItem(terminal, 0, "-" * 50, 0),
            TerminalItem(terminal, 0, "Video Maker ", 0),
            TerminalItem(terminal, 0, "-" * 50, 0),
            TerminalItem(terminal, self.LIVE_PROCESSES, "AI - Live Processes: ", 5),
            TerminalItem(terminal, self.AI_EXCEPTIONS, "AI - Exceptions: ", 5),
            TerminalItem(terminal, self.AI_IS_LIVE, "AI - Live: ", 5),
            TerminalItem(terminal, self.AI_DETECTIONS_PER_SECOND, "AI - Detections per second: ", 5),
            TerminalItem(terminal, self.AI_QUEUE_COUNT, "AI - Queue: ", 5),
            TerminalItem(terminal, self.VR_EXCEPTIONS, "VR - Exceptions: ", 5),
            TerminalItem(terminal, self.VR_RECORDING_START_SCHEDULED, "VR - Recording start scheduled: ", 5),
            TerminalItem(terminal, self.VR_RECORDING_STARTED, "VR - Recording started: ", 5),
            TerminalItem(terminal, self.VR_RECORDING_END_SCHEDULED, "VR - Recording end scheduled: ", 5),
            TerminalItem(terminal, self.VR_TOTAL_CAMERAS, "VR - Total Cameras: ", 5),
            TerminalItem(terminal, self.VR_HEART_BEAT, "VR - Live: ", 5),
            TerminalItem(terminal, self.VR_ACTIVE_CAMERA, "VR - Active Camera: ", 5),
            TerminalItem(terminal, self.VM_EXCEPTIONS, "VM - Exceptions: ", 5),
            TerminalItem(terminal, self.VM_WRITTEN_FRAMES, "VM - Written Frames: ", 5),
            TerminalItem(terminal, self.VM_QUEUE_COUNT, "VM - Queue: ", 5),
            TerminalItem(terminal, self.VM_IS_LIVE, "VM - Live: ", 5),
            TerminalItem(terminal, self.CURRENT_TASK, "Current Task: ", 80),
            TerminalItem(terminal, self.COMPLETED, "Completed: ", 80)
        ]

    def set_item_value(self, label_type: int, value):
        for item in self.terminal_items:
            if item.label_type == label_type:
                item.set_value(value)

    def increment_item_value(self, label_type: int, value):
        for item in self.terminal_items:
            if item.label_type == label_type:
                item.increment_value(value)

    def refresh(self):
        for item in self.terminal_items:
            item.refresh()

    @staticmethod
    def from_enum(enum_value: int) -> str:
        if enum_value == 1:
            return "LIVE_PROCESSES"
        if enum_value == 2:
            return "AI_EXCEPTIONS"
        if enum_value == 3:
            return "AI_IS_LIVE"
        if enum_value == 4:
            return "AI_DETECTIONS_PER_SECOND"
        if enum_value == 5:
            return "AI_QUEUE_COUNT"
        if enum_value == 6:
            return "VR_EXCEPTIONS"
        if enum_value == 7:
            return "VR_RECORDING_START_SCHEDULED"
        if enum_value == 8:
            return "VR_RECORDING_STARTED"
        if enum_value == 9:
            return "VR_RECORDING_END_SCHEDULED"
        if enum_value == 10:
            return "VR_TOTAL_CAMERAS"
        if enum_value == 12:
            return "VR_HEART_BEAT"
        if enum_value == 13:
            return "VR_ACTIVE_CAMERA"
        if enum_value == 14:
            return "VM_EXCEPTIONS"
        if enum_value == 15:
            return "VM_WRITTEN_FRAMES"
        if enum_value == 16:
            return "VM_QUEUE_COUNT"
        if enum_value == 17:
            return "ERROR_LOG"
        if enum_value == 18:
            return "CURRENT_TASK"
        if enum_value == 19:
            return "VM_IS_LIVE"
        if enum_value == 21:
            return "COMPLETED"
        return ""
