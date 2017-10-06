import logging

logger = logging.getLogger(__name__)


class Inspector:
    def __init__(self, filename, options):
        logger.debug("Initialising Inspector writer")

    def write(self, detector):
        # print all keys and values from detector structure
        # they include also a metadata read from binary output file
        for k, v in sorted(detector.__dict__.items()):
            print(k, v)
