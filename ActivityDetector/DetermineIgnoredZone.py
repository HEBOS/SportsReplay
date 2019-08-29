"""
    Usage: python3 DetermineIgnoredZone.py --image PNG_IMAGE_FULL_PATH  --camera CAMERA_ID

    Sample usage:
    python3 DetermineIgnoredZone.py --image  point-1.png --camera 1
"""
from graphics import *
import keyboard
from typing import List
import argparse
import tkinter as tk


class PolygonViewer(object):
    def __init__(self, image, camera):
        self.image_path = image
        self.camera = camera
        self.width = 1280
        self.height = 720
        self.ratio = 1280 / 480
        self.points: List[Point] = []
        self.mouseX = None
        self.mouseY = None
        self.win = GraphWin("Playground", width=self.width, height=self.height)
        self.background_image = tk.PhotoImage(file=self.image_path)
        self.draw_polygon()

        while True:
            if keyboard.is_pressed('c'):  # if key 'q' is pressed
                print('You Pressed C Key!')
                if len(self.points) > 0:
                    self.points.pop(len(self.points) - 1)
                self.draw_polygon()
            elif keyboard.is_pressed(chr(27)):  # if key 'q' is pressed:
                print('You Pressed ESC Key!')
                break  # finishing the loop
            else:
                if self.win.isOpen():
                    try:
                        point = self.win.getMouse()
                        if point is not None:
                            self.points.append(point)
                            self.draw_polygon()
                    except:
                        break

        print(self.generate_json())

    def draw_polygon(self):
        self.clear_window()
        self.win.flush()
        self.win.create_image(self.width/2, self.height/2, image=self.background_image)
        points = self.points
        poly = Polygon(*points)
        poly.setFill(color_rgb(255, 0, 255))
        poly.draw(self.win)

    def clear_window(self):
        for item in self.win.items[:]:
            item.undraw()
        self.win.update()

    def generate_json(self):
        json = "["
        for point in self.points:
            if len(json) > 1:
                json += ", "
            json += "{" + "\"x\": {}, \"y\": {}".format(int(point.x / self.ratio), int(point.y / self.ratio)) + "}"
        json += "]"

        return "{\"camera\": " + str(self.camera) + ", \"points\": " + json + "}"


if __name__ == "__main__":
    # parse the command line
    parser = \
        argparse.ArgumentParser(description="Determines the polygon, for AI detector to ignore.",
                                formatter_class=argparse.RawTextHelpFormatter,
                                epilog="Please run using: python3 DetermineIgnoredZone.py "
                                       "--image PNG_IMAGE_FULL_PATH "
                                       "--camera CAMERA_ID")

    parser.add_argument("--image", type=str, help="filename of the input image to process")
    parser.add_argument("--camera", type=int, default=None,
                        help="Camera id")

    try:
        opt, argv = parser.parse_known_args()
        PolygonViewer(opt.image, opt.camera)
    except Exception as ex:
        print(ex)
        parser.print_help()
        sys.exit(0)
