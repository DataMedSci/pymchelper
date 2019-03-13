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

    def write(self, detector):

        try:
            import h5py
        except ImportError as e:
            logger.error("Generating HDF5 files not available on your platform (please install h5py).")
            raise e

        with h5py.File(self.filename, 'w') as f:

            # change units for LET from MeV/cm to keV/um if necessary
            # a copy of data table is made here
            from pymchelper.shieldhit.detector.detector_type import SHDetType
            if detector.dettyp in (SHDetType.dlet, SHDetType.dletg, SHDetType.tlet, SHDetType.tletg):
                data = detector.data * np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um
                if not np.all(np.isnan(detector.error_raw)) and np.any(detector.error_raw):
                    error = detector.error * np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um
            else:
                data = detector.data
                error = detector.error

            # save data
            dset = f.create_dataset("data", data=data, compression="gzip", compression_opts=9)

            # save error (if present)
            if not np.all(np.isnan(detector.error_raw)) and np.any(detector.error_raw):
                f.create_dataset("error", data=error, compression="gzip", compression_opts=9)

            # save metadata
            dset.attrs['name'] = detector.name
            dset.attrs['unit'] = detector.unit
            dset.attrs['nstat'] = detector.nstat
            dset.attrs['counter'] = detector.counter
            dset.attrs['counter'] = detector.counter
            dset.attrs['xaxis_n'] = detector.x.n
            dset.attrs['xaxis_min'] = detector.x.min_val
            dset.attrs['xaxis_max'] = detector.x.max_val
            dset.attrs['xaxis_name'] = detector.x.name
            dset.attrs['xaxis_unit'] = detector.x.unit
            dset.attrs['yaxis_n'] = detector.y.n
            dset.attrs['yaxis_min'] = detector.y.min_val
            dset.attrs['yaxis_max'] = detector.y.max_val
            dset.attrs['yaxis_name'] = detector.y.name
            dset.attrs['yaxis_unit'] = detector.y.unit
            dset.attrs['zaxis_n'] = detector.z.n
            dset.attrs['zaxis_min'] = detector.z.min_val
            dset.attrs['zaxis_max'] = detector.z.max_val
            dset.attrs['zaxis_name'] = detector.z.name
            dset.attrs['zaxis_unit'] = detector.z.unit

        return 0
