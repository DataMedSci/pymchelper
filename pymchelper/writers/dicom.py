import datetime
import logging
from pathlib import Path

from pymchelper.estimator import Estimator
from pymchelper.page import Page

logger = logging.getLogger(__name__)


class DicomWriter:
    """
    Supports writing DICOM file format.

    """
    def __init__(self, filename : str, options):
        # ensure filename has dicom extension, if needed add it
        self.filename = Path(filename).with_suffix(".dcm")

    def write(self, estimator : Estimator):
        """TODO"""
        # save to single page to a file without number (i.e. output.dat)
        if len(estimator.pages) == 1:
            self.write_single_page(estimator.pages[0], self.filename)
        else:
            # create directory for output files if needed
            dir_path = self.filename.parent
            if not dir_path.exists():
                logger.info("Creating %s", dir_path)
                dir_path.mkdir(parents=True)

            # loop over all pages and save an image for each of them
            for i, page in enumerate(estimator.pages):

                # calculate output filename. it will include page number padded with zeros.
                # for 10-99 pages the filename would look like: output_p01.png, ... output_p99.png
                # for 100-999 pages the filename would look like: output_p001.png, ... output_p999.png
                zero_padded_page_no = str(i + 1).zfill(len(str(len(estimator.pages))))
                output_filename = f"{self.filename.stem}_p{zero_padded_page_no}{self.filename.suffix}"
                output_path = Path(dir_path, output_filename)

                # save the output file
                logger.info("Writing %s", output_path)
                self.write_single_page(page, output_path)

        return 0

    def write_single_page(self, page : Page, output_path : Path):
        """TODO"""
        logger.info("Attempt to write: %s", output_path)

        # special case for 0-dim data
        if page.dimension == 3:
            logger.info("Writing: %s", output_path)
            import pydicom
            from pydicom.dataset import FileDataset, FileMetaDataset
            from pydicom.uid import UID
            print("Setting file meta information...")
            # Populate required values for file meta information
            file_meta = FileMetaDataset()
            file_meta.MediaStorageSOPClassUID = UID('1.2.840.10008.5.1.4.1.1.2')
            file_meta.MediaStorageSOPInstanceUID = UID("1.2.3")
            file_meta.ImplementationClassUID = UID("1.2.3.4")

            print("Setting dataset values...")
            # Create the FileDataset instance (initially no data elements, but file_meta
            # supplied)
            ds = FileDataset(output_path, {},
                            file_meta=file_meta, preamble=b"\0" * 128)

            # Add the data elements -- not trying to set all required here. Check DICOM
            # standard
            ds.PatientName = "Test^Firstname"
            ds.PatientID = "123456"

            # Set the transfer syntax
            ds.is_little_endian = True
            ds.is_implicit_VR = True

            # Set creation date/time
            dt = datetime.datetime.now()
            ds.ContentDate = dt.strftime('%Y%m%d')
            timeStr = dt.strftime('%H%M%S.%f')  # long format with micro seconds
            ds.ContentTime = timeStr

            print("Writing test file", output_path)
            ds.save_as(output_path)
            print("File saved.")

        else:
            logger.error("Unsupported dimension: %d", page.dimension)
