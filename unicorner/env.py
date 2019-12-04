import logging


def get_logger(name):
    logger = logging.getLogger(name)
    logger.addHandler(logging.NullHandler())
    return logger


class UnicornerEnv:
    def __init__(self):
        self.score_overrides = {}
