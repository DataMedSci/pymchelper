import datetime
import logging
from pathlib import Path

import numpy as np
import pymchelper

from pymchelper.estimator import Estimator
from pymchelper.page import Page

logger = logging.getLogger(__name__)


class DicomWriter:
    """
    Supports writing DICOM file format.

    """

    def __init__(self, filename: str, options):
        # ensure filename has dicom extension, if needed add it
        self.filename = Path(filename).with_suffix(".dcm")
        self.ref_dicom_path = None
        if options.dicom:
            self.ref_dicom_path = Path(options.dicom)

    def write(self, estimator: Estimator):
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

    def write_single_page(self, page: Page, output_path: Path):
        """TODO"""
        logger.info("Attempt to write: %s", output_path)

        # special case for 0-dim data
        if page.dimension == 3:
            logger.info("Writing: %s", output_path)

            import pydicom
            from pydicom.dataset import FileDataset, FileMetaDataset
            from pydicom.uid import UID, RTDoseStorage, generate_uid

            # pydicom CLI is useful to inspect input and output DICOM files
            # see https://pydicom.github.io/pydicom/stable/guides/cli/cli_guide.html

            # Populate required values for file meta information
            logger.info("Creating file meta information")
            file_meta = FileMetaDataset()
            file_meta.MediaStorageSOPClassUID = RTDoseStorage
            file_meta.MediaStorageSOPInstanceUID = generate_uid(prefix=None)
            file_meta.ImplementationClassUID = generate_uid(prefix=None)

            if self.ref_dicom_path and self.ref_dicom_path.exists():
                logger.info("Using reference DICOM file: %s", self.ref_dicom_path)
                # copy some values from reference file into the meta info of the output file
                # we skip reading pixel data, as it is not needed here
                with pydicom.dcmread(self.ref_dicom_path, stop_before_pixels=True) as ref_ds:
                    file_meta.MediaStorageSOPInstanceUID = ref_ds.file_meta.MediaStorageSOPInstanceUID
                    logger.info("importing MediaStorageSOPInstanceUID: %s", file_meta.MediaStorageSOPInstanceUID)
                    file_meta.ImplementationClassUID = ref_ds.file_meta.ImplementationClassUID
                    logger.info("importing ImplementationClassUID: %s", file_meta.ImplementationClassUID)

            # Create the FileDataset instance
            ds = FileDataset(output_path, dataset={}, file_meta=file_meta, preamble=b"\0" * 128)

            ds.StudyInstanceUID = generate_uid(prefix=None)
            ds.SeriesInstanceUID = generate_uid(prefix=None)
            ds.Modality = 'RTDOSE'
            ds.StudyID = 'StudyID'
            ds.PatientName = "LastName^Firstname"
            ds.PatientID = "137"
            ds.Manufacturer = "pymchelper"
            ds.ManufacturerModelName = pymchelper.__version__

            # Set the transfer syntax
            ds.is_little_endian = True
            ds.is_implicit_VR = True

            # Set creation date/time
            dt = datetime.datetime.now()
            ds.ContentDate = dt.strftime('%Y%m%d')
            ds.ContentTime = dt.strftime('%H%M%S.%f')  # long format with micro seconds

            if self.ref_dicom_path and self.ref_dicom_path.exists():
                logger.info("Using reference DICOM file: %s", self.ref_dicom_path)
                # copy some values from reference file into the output file
                # we skip reading pixel data, as it is not needed here
                with pydicom.dcmread(self.ref_dicom_path, stop_before_pixels=True) as ref_ds:
                    ds.StudyInstanceUID = ref_ds.StudyInstanceUID
                    logger.info("importing StudyInstanceUID: %s", ds.StudyInstanceUID)
                    ds.SeriesInstanceUID = ref_ds.SeriesInstanceUID
                    logger.info("importing SeriesInstanceUID: %s", ds.SeriesInstanceUID)
                    ds.FrameOfReferenceUID = ref_ds.FrameOfReferenceUID
                    logger.info("importing FrameOfReferenceUID: %s", ds.FrameOfReferenceUID)
                    ds.PatientName = ref_ds.PatientName
                    logger.info("importing PatientName: %s", ds.PatientName)
                    ds.PatientID = ref_ds.PatientID
                    logger.info("importing PatientID: %s", ds.PatientID)
                    ds.StudyID = ref_ds.StudyID
                    logger.info("importing StudyID: %s", ds.StudyID)

            '''
            Good desciprion of coordinate systems is found in 
            Bush, Karl K., and Sergei F. Zavgorodni. "IEC accelerator beam coordinate transformations for clinical 
            Monte Carlo simulation from a phase space or full BEAMnrc particle source." 
            Australasian physical & engineering sciences in medicine 33.4 (2010): 351-355.
            '''

            if page.data is not None and len(page.data.shape) == 5:
                mc_3d_data = page.data[:,:,:,0,0]
                first_swap = np.swapaxes(mc_3d_data, 1, 2)  # DICOM Y = MC Z, DICOM Z = MC Y
                second_swap = np.swapaxes(first_swap, 0, 2) # DICOM X = MC Y, DICOM Y = MC Z, DICOM Z = MC X

                mc_dx = page.axis(0).data[1] - page.axis(0).data[0]
                mc_dy = page.axis(1).data[1] - page.axis(1).data[0]
                mc_dz = page.axis(2).data[1] - page.axis(2).data[0]

                dicom_dx = mc_dy
                dicom_dy = mc_dz
                dicom_dz = mc_dx

                ds.ImagePositionPatient = [page.axis(1).data[0], page.axis(2).data[0], page.axis(0).data[0]]  # Y, Z, X
                ds.PixelSpacing = [dicom_dy, dicom_dz]
                ds.GridFrameOffsetVector = np.arange(start=0, stop=page.axis(1).data[-1], step=mc_dx).tolist()

                # write 3D numpy array to DICOM file
                ds.PixelData = second_swap.tobytes()

            logger.info("Writing: %s", output_path)
            ds.save_as(output_path)
            logger.info("Writed: %s", output_path)

        else:
            logger.error("Unsupported dimension: %d", page.dimension)
