#!/usr/bin/env python3
import threading
import argparse



class Play(object):
    def __init__(self):
        self.dispatching = True
        self.dispatch_lock = threading.Lock()

    def start(self, debugging: bool):
        outgoing_pipeline = "filesrc location={location} " \
                            "! qtdemux " \
                            "! queue " \
                            "! h264parse " \
                            "! omxh264dec " \
                            "! video/x-raw,format=NV12,width=1280,height=720,framerate=25/1 " \
                            "! videoconvert " \
                            "! nvoverlaysink -e".format(location=location,
                                                        fps=fps,
                                                        width=width,
                                                        height=height)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sports Replay Player",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog="Please run using: python3 Play.py --debug true")

    parser.add_argument("--debug", type=int, default=0, help="True for debugging.")
    opt, argv = parser.parse_known_args()
    Play().start(opt.debug == 1)
