class YoloDetection(object):
    def __init__(self, class_id, class_name, confidence, left, top, width, height):
        self.ClassName: str = class_name
        self.ClassID: int = class_id
        self.Confidence: float = confidence
        self.Left: float = left
        self.Right: float = left + width
        self.Top: float = top
        self.Bottom: float = top + height
        self.Width: float = width
        self.Height: float = height
