import os
import logging

from Shared.Configuration import Configuration


class LogHandler(object):
    def __init__(self, application):
        config = Configuration()
        path = config.common["log-files"]

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename=os.path.normpath('{}/sports-replay-{}-info.log'.format(path, application)),
                            filemode='w')

        self.logger = logging.getLogger(application)
        error_handler = logging.FileHandler(os.path.normpath('{}/sports-replay-{}-error.log'.format(path, application)))
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)

        info_handler = logging.FileHandler(os.path.normpath('{}/sports-replay-{}-info.log'.format(path, application)))
        info_handler.setLevel(logging.INFO)
        self.logger.addHandler(info_handler)

        warning_handler = logging.FileHandler(
            os.path.normpath('{}/sports-replay-{}-warning.log'.format(path, application)))
        warning_handler.setLevel(logging.WARNING)
        self.logger.addHandler(warning_handler)

    def warning(self, message):
        print(message)
        # self.logger.warning(message)

    def error(self, message):
        print(message)
        # self.logger.error(message)

    def info(self, message):
        print(message)
        # self.logger.info(message)

