import logging

from pymchelper.axis import AxisId
from pymchelper.estimator import Estimator

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

    def write(self, estimator: Estimator):
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
                if page.error is not None:
                    hdf_file.create_dataset(dataset_error_name, data=page.error, compression="gzip", compression_opts=9)

                # save metadata
                dset.attrs['name'] = page.name
                dset.attrs['unit'] = page.unit
                dset.attrs['nstat'] = estimator.number_of_primaries
                dset.attrs['counter'] = estimator.file_counter
                # mesh is taken from the page, FLUKA pages in one file can have different meshes
                x_axis = page.axis(AxisId.x)
                y_axis = page.axis(AxisId.y)
                z_axis = page.axis(AxisId.z)
                dset.attrs['xaxis_n'] = x_axis.n
                dset.attrs['xaxis_min'] = x_axis.min_val
                dset.attrs['xaxis_max'] = x_axis.max_val
                dset.attrs['xaxis_name'] = x_axis.name
                dset.attrs['xaxis_unit'] = x_axis.unit
                dset.attrs['yaxis_n'] = y_axis.n
                dset.attrs['yaxis_min'] = y_axis.min_val
                dset.attrs['yaxis_max'] = y_axis.max_val
                dset.attrs['yaxis_name'] = y_axis.name
                dset.attrs['yaxis_unit'] = y_axis.unit
                dset.attrs['zaxis_n'] = z_axis.n
                dset.attrs['zaxis_min'] = z_axis.min_val
                dset.attrs['zaxis_max'] = z_axis.max_val
                dset.attrs['zaxis_name'] = z_axis.name
                dset.attrs['zaxis_unit'] = z_axis.unit

        return 0
