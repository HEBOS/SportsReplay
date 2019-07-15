import threading
import cv2

from Shared.LogHandler import LogHandler

class VideoCaptureAsync:
    def __init__(self, src="", width=640, height=480, fps=30):
        self.src = src
        self.cap = cv2.VideoCapture(self.src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.grabbed, self.frame = self.cap.read()
        self.started = False
        self.read_lock = threading.Lock()
        self.logger = LogHandler("recording")

    def set(self, var1, var2):
        self.cap.set(var1, var2)

    def start(self):
        if self.started:
            print('[!] Threaded video capturing has already been started.')
            return None
        self.started = True
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.start()
        return self

    def update(self):
        while self.started:
            try:
                grabbed, frame = self.cap.read()
                with self.read_lock:
                    self.grabbed = grabbed
                    self.frame = frame
            except cv2.error as e:
                self.logger.error("Camera {}, on playground {} is not responding."
                                  .format(self.camera_number, self.playground))

    def read(self):
        with self.read_lock:
            frame = self.frame.copy()
            grabbed = self.grabbed
        return grabbed, frame

    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exec_type, exc_value, traceback):
        self.cap.release()
