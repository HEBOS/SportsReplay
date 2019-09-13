import numpy
from Darknet.DarknetBindings import *
from Shared.YoloDetection import YoloDetection
from typing import List


class DarknetDetector(object):
    def __init__(self, cfg_path: str, weights_path: str, classnames_path: str):
        self._net = load_net(c_char_p(cfg_path.encode("utf-8")),
                             c_char_p(weights_path.encode("utf-8")),
                             0)
        self._meta = load_meta(c_char_p(classnames_path.encode("utf-8")))
        self.darknet_image = make_image(lib.network_width(self._net), lib.network_height(self._net), 3)

    def detect(self, img: numpy.array, display_results: bool) -> List[YoloDetection]:
        frame_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (lib.network_width(self._net),
                                               lib.network_height(self._net)),
                                   interpolation=cv2.INTER_LINEAR)
        copy_image_from_bytes(self.darknet_image, frame_resized.tobytes())
        result = detect(self._net, self._meta, self.darknet_image)
        if display_results:
            print("")
            print("")

            if len(result) == 0:
                print("No objects detected")
            else:
                print("There are {} objects detected:".format(len(result)))
                for detection in result:
                    print("Detected [Class='{}', Confidence={}%, X={}, Y={}, Width={}, Height={}]".format(
                        str(detection.ClassName),
                        int(detection.Confidence * 100),
                        int(detection.Left),
                        int(detection.Top),
                        int(detection.Width),
                        int(detection.Height)
                    ))

        return result

