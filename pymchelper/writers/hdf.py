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
        if len(estimator.pages) == 0:
            print("No pages in the output file, conversion to HDF5 skipped.")
            return False

        try:
            import h5py
        except ImportError as e:
            logger.error("Generating HDF5 files not available on your platform (please install h5py).")
            raise e

        with h5py.File(self.filename, 'w') as hdf_file:

            for page_number, page in enumerate(estimator.pages):

                dataset_name = "data"
                dataset_error_name = "error"
                if len(estimator.pages) > 1:
                    dataset_name += f"_{page_number}"
                    dataset_error_name += f"_{page_number}"

                # save data
                dset = hdf_file.create_dataset(dataset_name, data=page.data, compression="gzip", compression_opts=9)

                # save error (if present)
                if not np.all(np.isnan(page.error_raw)) and np.any(page.error_raw):
                    hdf_file.create_dataset(dataset_error_name, data=page.error, compression="gzip", compression_opts=9)

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
