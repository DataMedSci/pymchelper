import logging

logger = logging.getLogger(__name__)


class Inspector:
    def __init__(self, filename, options):
        logger.debug("Initialising Inspector writer")

    def write(self, detector):
        # print all keys and values from detector structure
        # they include also a metadata read from binary output file
        for name, value in sorted(detector.__dict__.items()):
            line = "{:24s}: '{:s}'".format(str(name), str(value))
            print(line)
