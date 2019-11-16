import cv2
import numpy as np
import time


class LogoRenderer(object):
    @staticmethod
    def draw_logo(background: np.ndarray, overlay: np.ndarray, date_format: str, time_format: str, camera_time: time):
        rect_overlay = background.copy()
        rows, cols, channels = overlay.shape

        brows, bcols, bchannels = background.shape
        multiplier = bcols / 1280

        edge = int(10 * multiplier)
        logo_start_y = int(20 * multiplier)
        logo_end_y = int(20 * multiplier) + rows
        logo_start_x = int(20 * multiplier)
        logo_end_x = int(20 * multiplier) + cols

        rect_start_x = logo_start_x - edge
        rect_end_x = logo_start_x + cols + int(100 * multiplier) + edge
        rect_start_y = logo_start_x - edge
        rect_end_y = logo_start_y + rows + edge

        cv2.rectangle(background, (rect_start_x, rect_start_y), (rect_end_x, rect_end_y), (0, 0, 0), -1)
        modified_rect_overlay = cv2.addWeighted(rect_overlay[rect_start_y:rect_end_y, rect_start_x:rect_end_x], 0.2,
                                                background[rect_start_y:rect_end_y, rect_start_x:rect_end_x], 0.8, 0)
        background[rect_start_y:rect_end_y, rect_start_x:rect_end_x] = modified_rect_overlay.copy()
        modified_rect_overlay = None
        del modified_rect_overlay

        modified_overlay = cv2.addWeighted(background[logo_start_y:logo_end_y,
                                           logo_start_x:logo_end_x],
                                           1,
                                           overlay,
                                           1,
                                           0)
        background[logo_start_y:logo_end_y, logo_start_x:logo_end_x] = modified_overlay.copy()
        modified_overlay = None
        del modified_overlay

        cv2.putText(background,
                    time.strftime(date_format, camera_time),
                    (int(150 * multiplier),
                     int(34 * multiplier)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5 * multiplier,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                    False)

        cv2.putText(background,
                    time.strftime(time_format, camera_time),
                    (int(159 * multiplier),
                     int(60 * multiplier)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5 * multiplier,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                    False)

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
    def get_resized_overlay(logo_path: str, resolution: int) -> np.ndarray:
        overlay = cv2.imread(logo_path, cv2.IMREAD_COLOR)
        rows, cols, channels = overlay.shape
        height = int(rows / 1.5 * resolution / 1280)
        return LogoRenderer.image_resize(overlay, height=height)




