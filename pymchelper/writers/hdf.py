import logging
import numpy as np

logger = logging.getLogger(__name__)


class HdfWriter:
    """
    Supports writing HDF file format.
    HDF is designed to store large amounts of data organized in convenient way.
    One HDF file can handle many single- or multi-dimensional tables.

    """
    def __init__(self, filename, options):
        self.filename = filename
        if not self.filename.endswith(".h5"):
            self.filename += ".h5"

    def write(self, estimator):
        if len(estimator.pages) > 1:
            print("Conversion of data with multiple pages not supported yet")
            return False

        try:
            import h5py
        except ImportError as e:
            logger.error("Generating HDF5 files not available on your platform (please install h5py).")
            raise e

        with h5py.File(self.filename, 'w') as f:

            # change units for LET from MeV/cm to keV/um if necessary
            # a copy of data table is made here
            # from pymchelper.shieldhit.detector.detector_type import SHDetType
            # if estimator.dettyp in (SHDetType.dlet, SHDetType.dletg, SHDetType.tlet, SHDetType.tletg):
            #     data = estimator.data * np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um
            #     if not np.all(np.isnan(estimator.error_raw)) and np.any(estimator.error_raw):
            #         error = estimator.error * np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um
            # else:
            #     data = estimator.data
            #     error = estimator.error
            # TODO move to reader

            page = estimator.pages[0]
            data = page.data
            error = page.error

            # save data
            dset = f.create_dataset("data", data=data, compression="gzip", compression_opts=9)

            # save error (if present)
            if not np.all(np.isnan(page.error_raw)) and np.any(page.error_raw):
                f.create_dataset("error", data=error, compression="gzip", compression_opts=9)

            # save metadata
            dset.attrs['name'] = page.name
            dset.attrs['unit'] = page.unit
            dset.attrs['nstat'] = estimator.number_of_primaries
            dset.attrs['counter'] = estimator.file_counter
            dset.attrs['xaxis_n'] = estimator.x.n
            dset.attrs['xaxis_min'] = estimator.x.min_val
            dset.attrs['xaxis_max'] = estimator.x.max_val
            dset.attrs['xaxis_name'] = estimator.x.name
            dset.attrs['xaxis_unit'] = estimator.x.unit
            dset.attrs['yaxis_n'] = estimator.y.n
            dset.attrs['yaxis_min'] = estimator.y.min_val
            dset.attrs['yaxis_max'] = estimator.y.max_val
            dset.attrs['yaxis_name'] = estimator.y.name
            dset.attrs['yaxis_unit'] = estimator.y.unit
            dset.attrs['zaxis_n'] = estimator.z.n
            dset.attrs['zaxis_min'] = estimator.z.min_val
            dset.attrs['zaxis_max'] = estimator.z.max_val
            dset.attrs['zaxis_name'] = estimator.z.name
            dset.attrs['zaxis_unit'] = estimator.z.unit

        return 0
