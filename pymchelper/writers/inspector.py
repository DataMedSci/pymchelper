import logging

logger = logging.getLogger(__name__)


class Inspector:
    def __init__(self, filename, options):
        logger.debug("Initialising Inspector writer")

    def write(self, detector):
        # print all keys and values from detector structure
        # they include also a metadata read from binary output file
        for name, value in sorted(detector.__dict__.items()):
            # be careful not to check for np.array but for np.ndarray!
            if name not in ('data', 'error', 'counter'):  # skip non-metadata fields
                line = "{:24s}: '{:s}'".format(str(name), str(value))
                print(line)
        # print some data-related statistics
        print(32 * "-")
        print("Data min: {:g}, max: {:g}".format(detector.data.min(), detector.data.max()))
