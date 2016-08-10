import logging

import numpy as np

from pymchelper.shieldhit.detector.estimator_type import SHGeoType

logger = logging.getLogger(__name__)


class SHBinaryWriter:
    def __init__(self, filename):
        self.filename = filename

    def write(self, detector):
        # TODO
        pass


class SHFortranWriter:
    @staticmethod
    def _axis_name(geo_type, axis_no):
        cyl = ['R', 'PHI', 'Z']
        msh = ['X', 'Y', 'Z']
        if geo_type in (SHGeoType.cyl, SHGeoType.dcyl):
            return cyl[axis_no]
        else:
            return msh[axis_no]

    def __init__(self, filename):
        self.filename = filename

    def write(self, det):
        from pymchelper.fortranformatter import format_d, format_e
        header = "#   DETECTOR OUTPUT\n"
        ax = self._axis_name(det.geotyp, 0)
        ay = self._axis_name(det.geotyp, 1)
        az = self._axis_name(det.geotyp, 2)
        header += "#   {:s} BIN:{:6d} {:s} BIN:{:6d} {:s} BIN:{:6d}\n".format(ax, det.nx, ay, det.ny, az, det.nz)
        header += "#   JPART:{:6d} DETECTOR TYPE:{:s}\n".format(det.particle, str(det.dettyp).ljust(10))
        header += "#   {:s} START:{:s}".format(ax, format_d(10, 3, det.xmin))
        header += " {:s} START:{:s}".format(ay, format_d(10, 3, det.ymin))
        header += " {:s} START:{:s}\n".format(az, format_d(10, 3, det.zmin))
        header += "#   {:s} END  :{:s}".format(ax, format_d(10, 3, det.xmax))
        header += " {:s} END  :{:s}".format(ay, format_d(10, 3, det.ymax))
        header += " {:s} END  :{:s}\n".format(az, format_d(10, 3, det.zmax))
        header += "#   PRIMARIES:" + format_d(10, 3, det.nstat) + "\n"
        with open(self.filename, 'w') as fout:
            logger.info("Writing: " + self.filename)
            fout.write(header)
            for x, y, z, v in zip(det.x, det.y, det.z, det.data):
                x = float('nan') if np.isnan(x) else x
                y = float('nan') if np.isnan(y) else y
                z = float('nan') if np.isnan(z) else z
                v = float('nan') if np.isnan(v) else v
                tmp = format_e(14, 7, x) + " " + \
                    format_e(14, 7, y) + " " + \
                    format_e(14, 7, z) + " " + \
                    format_e(23, 16, v) + "\n"
                fout.write(tmp)
