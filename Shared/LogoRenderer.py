import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image
import time


class LogoRenderer(object):
    @staticmethod
    def write(background: np.ndarray, overlay: np.ndarray, font: ImageFont.FreeTypeFont,
              date_format: str, time_format: str, current_time: time) -> np.ndarray:
        rect_overlay = background.copy()
        rows, cols, channels = overlay.shape

        edge = 10
        logo_start_y = 20
        logo_end_y = 20 + rows
        logo_start_x = 20
        logo_end_x = 20 + cols

        rect_start_x = logo_start_x - edge
        rect_end_x = logo_start_x + cols + 100 + edge
        rect_start_y = logo_start_x - edge
        rect_end_y = logo_start_y + rows + edge

        cv2.rectangle(background, (rect_start_x, rect_start_y), (rect_end_x, rect_end_y), (0, 0, 0), -1)
        rect_overlay = cv2.addWeighted(rect_overlay[rect_start_y:rect_end_y, rect_start_x:rect_end_x], 0.2,
                                       background[rect_start_y:rect_end_y, rect_start_x:rect_end_x], 0.8, 0)
        background[rect_start_y:rect_end_y, rect_start_x:rect_end_x] = rect_overlay

        overlay = cv2.addWeighted(background[logo_start_y:logo_end_y, logo_start_x:logo_end_x], 1, overlay, 1, 0)
        background[logo_start_y:logo_end_y, logo_start_x:logo_end_x] = overlay

        background = Image.fromarray(cv2.cvtColor(background, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(background)
        draw.text((155, 20),
                  time.strftime(date_format, time.localtime(current_time)),
                  font=font, fill=(255, 255, 255))
        draw.text((164, 45), time.strftime(time_format, time.localtime(current_time)),
                  font=font, fill=(255, 255, 255))
        background = cv2.cvtColor(np.array(background), cv2.COLOR_RGB2BGR)
        return background

    @staticmethod
    def image_resize(image, width=None, height=None, inter=cv2.INTER_AREA):
        # initialize the dimensions of the image to be resized and
        # grab the image size
        dim = None
        (h, w) = image.shape[:2]

        # if both the width and height are None, then return the
        # original image
        if width is None and height is None:
            return image

        # check to see if the width is None
        if width is None:
            # calculate the ratio of the height and construct the
            # dimensions
            r = height / float(h)
            dim = (int(w * r), height)

        # otherwise, the height is None
        else:
            # calculate the ratio of the width and construct the
            # dimensions
            r = width / float(w)
            dim = (width, int(h * r))

        # resize the image
        resized = cv2.resize(image, dim, interpolation = inter)

        # return the resized image
        return resized

    @staticmethod
    def get_logo_font(font_path: str) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(font_path, 18)

    @staticmethod
    def get_resized_overlay(logo_path: str, resolution: int) -> np.ndarray:
        overlay = cv2.imread(logo_path, cv2.IMREAD_COLOR)
        rows, cols, channels = overlay.shape
        height = int(rows / 1.5 * resolution / 1280)
        return LogoRenderer.image_resize(overlay, height=height)



