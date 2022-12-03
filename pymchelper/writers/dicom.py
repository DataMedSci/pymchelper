import logging

logger = logging.getLogger(__name__)


class DicomWriter:
    """
    Supports writing DICOM file format.

    """
    def __init__(self, filename, options):
        self.filename = filename
        if not self.filename.endswith(".dcm"):
            self.filename += ".dcm"

    def write(self, estimator):
        print("tadam")
        return 0
