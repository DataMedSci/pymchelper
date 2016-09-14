import logging
import numpy as np

logger = logging.getLogger(__name__)


class SHTripCubeWriter:
    def __init__(self, filename):
        self.output_corename = filename

    def write(self, detector):
        from pymchelper.shieldhit.detector.detector_type import SHDetType

        pixel_size_x = (detector.xmax - detector.xmin) / detector.nx
        pixel_size_z = (detector.zmax - detector.zmin) / detector.nz

        if detector.dettyp == SHDetType.dose:

            from pytrip import dos

            cube = dos.DosCube()
            cube.create_empty_cube(
                1.0, detector.nx, detector.ny, detector.nz,
                pixel_size=pixel_size_x, slice_distance=pixel_size_z)

            # .dos dose cubes are usually in normalized integers,
            # where "1000" equals 100.0 % dose.
            # The next are also the defaults, but just to be clear
            # this is specifially set.
            cube.data_type = "integer"
            cube.bytes = 2
            cube.pydata_type = np.int16

            cube.cube = detector.data.reshape(detector.nx, detector.ny, detector.nz)

            if detector.tripdose >= 0.0 and detector.tripntot > 0:
                cube.cube = (cube.cube * detector.tripntot * 1.602e-10) / detector.tripdose * 1000.0
            else:
                cube.cube = (cube.cube / cube.cube.max()) * 1200.0

            cube.write(self.output_corename)

        elif detector.dettyp in (SHDetType.dlet, SHDetType.tlet, SHDetType.dletg, SHDetType.tletg):

            from pytrip import let

            cube = let.LETCube()
            cube.create_empty_cube(
                1.0, detector.nx, detector.ny, detector.nz,
                pixel_size=pixel_size_x,
                slice_distance=pixel_size_z)

            # .dosemlet.dos LET cubes are usually in 32 bit floats.
            cube.data_type = "float"
            cube.bytes = 4
            cube.pydata_type = np.float32

            # need to redo the cube, since by default np.float32 are allocated.
            # When https://github.com/pytrip/pytrip/issues/35 is fixed,
            # then this should not be needed.
            cube.cube = np.ones((cube.dimz, cube.dimy, cube.dimx), dtype=cube.pydata_type) * (1.0)

            cube.cube = detector.data.reshape(detector.nx, detector.ny, detector.nz)
            cube.cube *= 0.1  # MeV/cm -> keV/um

            cube.write(self.output_corename)

        else:
            logger.error("Tripcube target is only allowed with dose- or LET-type detectors.")
            raise Exception("Illegal detector for tripcube.")
