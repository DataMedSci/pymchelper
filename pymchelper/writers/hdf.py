import logging

logger = logging.getLogger(__name__)


class HdfWriter:
    """
    Supports writing HDF file format
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
            dset = f.create_dataset("data", data=detector.data)
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
