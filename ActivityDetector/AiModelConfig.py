from Shared.Configuration import Configuration
from Mask_RCNN.mrcnn.config import Config


class AiModelConfig(Config):

    labels = Configuration().activity_detector["labels"]
    CLASS_NAMES = open(labels).read().strip().split("\n")
    # give the configuration a recognizable name
    NAME = "coco_inference"

    # set the number of GPUs to use along with the number of images
    # per GPU
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1

    # number of classes (we would normally add +1 for the background
    # but the background class is *already* included in the class
    # names)
    NUM_CLASSES = len(CLASS_NAMES)

    # Currently supported: ['resnet50','resnet101', 'mobilenetv1','mobilenetv2']
    BACKBONE = "mobilenetv1"
    # USE_MULTIPROCESSING = True
