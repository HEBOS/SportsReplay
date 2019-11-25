#!/usr/bin/env python3
import cv2


class CvFunctions(object):
    @staticmethod
    def release_open_cv():
        try:
            cv2.waitKey(1)
            cv2.destroyAllWindows()
            for i in range(1, 5):
                cv2.waitKey(1)
        except:
            pass

