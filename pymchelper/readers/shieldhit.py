import logging

import numpy as np
from enum import IntEnum

from pymchelper.shieldhit.detector.detector import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

logger = logging.getLogger(__name__)


class SHConverters(IntEnum):
    standard = 0
    plotdata = 1
    gnuplot = 2
    image = 3
    tripcube = 4


class SHBinaryReader:
    def __init__(self, filename):
        self.filename = filename

    def read_header(self, detector):
        logger.info("Reading header: " + self.filename)

        detector.tripdose = 0.0
        detector.tripntot = -1

        # effective read
        # first figure out if this is a VOXSCORE card
        header_dtype = np.dtype([('fo1', '<i4'), ('geotyp', 'S10')])
        header = np.fromfile(self.filename, header_dtype, count=1)

        if 'VOXSCORE' in header['geotyp'][0].decode('ascii'):
            header_dtype = np.dtype([('fo1', '<i4'),
                                     ('geotyp', 'S10'),
                                     ('fo2', '<i4'),  # nstat
                                     ('fo3', '<i4'),
                                     ('nstat', '<i4'),
                                     ('tds', '<f4'),  # tripdose
                                     ('tnt', '<i8'),  # tripntot
                                     ('fo4', '<i8'),
                                     ('fo5', '<i8'),
                                     ('det', ('<f8', 8)),
                                     ('fo6', '<i8'),
                                     ('fo7', '<i8'),
                                     ('idet', '<i4', 11),
                                     ('fo8', '<i4'),
                                     ('reclen', '<i4')])
        else:
            # first figure out the length.
            header_dtype = np.dtype([('fo1', '<i4'), ('geotyp', 'S10'), ('fo2', '<i4'), ('fo3', '<i4'),
                                     ('nstat', '<i4'), ('fo4', '<i4'), ('fo5', '<i4'), ('det',
                                                                                        ('<f8', 8)), ('fo6', '<i4'),
                                     ('fo7', '<i4'), ('idet', '<i4', 11), ('fo8', '<i4'), ('reclen', '<i4')])
        header = np.fromfile(self.filename, header_dtype, count=1)
        detector.rec_size = header['reclen'][0] // 8

        if 'VOXSCORE' in header['geotyp'][0].decode('ascii'):
            detector.tripdose = header['tds']
            detector.tripntot = header['tnt']

        idet = header['idet']

        detector.nx = idet[0][0]
        detector.ny = idet[0][1]
        detector.nz = idet[0][2]

        detector.det = header['det']
        detector.particle = idet[0][3]

        try:
            detector.geotyp = SHGeoType[header['geotyp'][0].decode('ascii').strip().lower()]
        except Exception:
            detector.geotyp = SHGeoType.unknown
        detector.nstat = header['nstat'][0]

        shift = 0
        if 'VOXSCORE' in header['geotyp'][0].decode('ascii'):
            shift = 1
            # TODO to be investigated
        detector.xmin = header['det'][0][0 + shift]
        detector.ymin = header['det'][0][1 + shift]
        detector.zmin = header['det'][0][2 + shift]

        detector.xmax = header['det'][0][3 + shift]
        detector.ymax = header['det'][0][4 + shift]
        detector.zmax = header['det'][0][5 + shift]

        detector.dettyp = SHDetType(idet[0][4])

    def read_payload(self, detector):
        logger.info("Reading data: " + self.filename)

        if detector.geotyp == SHGeoType.unknown or detector.dettyp == SHDetType.unknown:
            detector.data = []
            return

        # next read the data:
        record_dtype = np.dtype([('trash', ('S158')), ('bin2', ('<f8'), detector.rec_size)])
        record = np.fromfile(self.filename, record_dtype, count=-1)
        detector.data = record['bin2'][:][0]
        if detector.dimension == 0:
            detector.data = np.asarray([detector.data])

        if detector.geotyp == SHGeoType.plane:
            detector.data = np.asarray([detector.data])

        # normalize result if we need that.
        if detector.dettyp not in (SHDetType.dlet, SHDetType.tlet, SHDetType.avg_energy, SHDetType.avg_beta,
                                   SHDetType.material):
            detector.data /= np.float64(detector.nstat)

        detector.counter = 1

    def read(self, detector):
        self.read_header(detector)
        self.read_payload(detector)


class SHFortranReader:
    def __init__(self, filename):
        self.filename = filename

    def read_header(self, detector):
        # TODO
        pass

    def read_payload(self, detector):
        # TODO
        pass

    def read(self, detector):
        self.read_header(detector)
        self.read_payload(detector)
