import numpy
from Darknet.DarknetBindings import *


class DarknetDetector(object):
    def __init__(self, cfg_path: str, weights_path: str, classnames_path: str):
        self._net = load_net(c_char_p(os.path.join(os.getcwd(), cfg_path).encode("utf-8")),
                             c_char_p(os.path.join(os.getcwd(), weights_path).encode("utf-8")),
                             0)
        self._meta = load_meta(c_char_p(os.path.join(os.getcwd(), classnames_path).encode("utf-8")))

    def detect(self, img: numpy.array):
        print(detect(self._net, self._meta, img))


