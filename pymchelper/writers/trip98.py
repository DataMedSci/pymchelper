import logging

logger = logging.getLogger(__name__)


class SHTripCubeWriter:
    def __init__(self, filename):
        self.output_corename = filename

    def write(self, detector):
        from pytrip import dos
        cube = dos.DosCube()
        pixel_size_x = (detector.xmax - detector.xmin) / detector.nx
        pixel_size_z = (detector.zmax - detector.zmin) / detector.nz
        cube.create_empty_cube(
            1.0, detector.nx, detector.ny, detector.nz, pixel_size=pixel_size_x, slice_distance=pixel_size_z)
        cube.cube = detector.data.reshape(detector.nx, detector.ny, detector.nz)
        if detector.tripdose >= 0.0 and detector.tripntot > 0:
            cube.cube = (cube.cube * detector.tripntot * 1.602e-10) /\
                detector.tripdose * 1000.0
        else:
            cube.cube = (cube.cube / cube.cube.max()) * 1200.0

        cube.write(self.output_corename)
