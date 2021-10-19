import logging
import numpy as np

logger = logging.getLogger(__name__)


class TRiP98CubeWriter:
    def __init__(self, filename, options):
        self.output_corename = filename

    def write(self, estimator):
        if len(estimator.pages) > 1:
            print("Conversion of data with multiple pages not supported yet")
            return False

        import getpass
        from pymchelper.shieldhit.detector.detector_type import SHDetType
        from pymchelper import __version__ as _pmcversion
        try:
            from pytrip import __version__ as _ptversion
        except ImportError:
            logger.error("pytrip package missing, to install type `pip install pytrip98`")
            return 1

        pixel_size_x = (estimator.x.max_val - estimator.x.min_val) / estimator.x.n
        pixel_size_z = (estimator.z.max_val - estimator.z.min_val) / estimator.z.n

        logging.debug("psx: {:.6f} [cm]".format(pixel_size_x))
        logging.debug("psz: {:.6f} [cm]".format(pixel_size_z))

        _patient_name = "Anonymous"
        _created_by = getpass.getuser()
        _creation_info = "Created with pymchelper {:s}; using PyTRiP98 {:s}".format(_pmcversion,
                                                                                    _ptversion)

        if estimator.pages[0].dettyp == SHDetType.dose:

            from pytrip import dos

            cube = dos.DosCube()
            # Warning: PyTRiP cube dimensions are in [mm]
            cube.create_empty_cube(
                1.0, estimator.x.n, estimator.y.n, estimator.z.n,
                pixel_size=pixel_size_x * 10.0,
                slice_distance=pixel_size_z * 10.0)

            # .dos dose cubes are usually in normalized integers,
            # where "1000" equals 100.0 % dose.
            # The next are also the defaults, but just to be clear
            # this is specifically set.
            cube.data_type = "integer"
            cube.num_bytes = 2
            cube.pydata_type = np.int16

            cube.cube = estimator.data

            if estimator.tripdose >= 0.0 and estimator.tripntot > 0:
                cube.cube = (cube.cube * estimator.tripntot * 1.602e-10) / estimator.tripdose * 1000.0
            else:
                cube.cube = (cube.cube / cube.cube.max()) * 1200.0

            # Save proper meta information
            cube.patient_name = _patient_name
            cube.created_by = _created_by
            cube.creation_info = _creation_info

            cube.write(self.output_corename)

            return 0

        elif estimator.pages[0].dettyp in (SHDetType.dlet, SHDetType.tlet, SHDetType.dletg, SHDetType.tletg):

            from pytrip import let

            cube = let.LETCube()
            # Warning: PyTRiP cube dimensions are in [mm]
            cube.create_empty_cube(
                1.0, estimator.x.n, estimator.y.n, estimator.z.n,
                pixel_size=pixel_size_x * 10.0,
                slice_distance=pixel_size_z * 10.0)

            # .dosemlet.dos LET cubes are usually in 32 bit floats.
            cube.data_type = "float"
            cube.num_bytes = 4
            cube.pydata_type = np.float32

            # need to redo the cube, since by default np.float32 are allocated.
            # When https://github.com/pytrip/pytrip/issues/35 is fixed,
            # then this should not be needed.
            cube.cube = np.ones((cube.dimz, cube.dimy, cube.dimx), dtype=cube.pydata_type)

            cube.cube = estimator.data
            cube.cube *= 0.1  # MeV/cm -> keV/um
            # Save proper meta information

            cube.patient_name = _patient_name
            cube.created_by = _created_by
            cube.creation_info = _creation_info

            cube.write(self.output_corename)

            return 0

        else:
            logger.error("Tripcube target is only allowed with dose- or LET-type detectors.")
            raise Exception("Illegal detector for tripcube.")
