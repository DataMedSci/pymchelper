import logging

import numpy as np

from pymchelper.shieldhit.detector.detector_type import SHDetType
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

        # first line with detector geo type
        if det.geotyp in (SHGeoType.plane, SHGeoType.dplane, ):
            header = "#             DETECTOR OUTPUT PLANE/DPLANE\n"
        elif det.geotyp in (SHGeoType.zone, SHGeoType.dzone, ):
            header = "#             DETECTOR OUTPUT ZONE/DZONE\n"
        elif det.geotyp in (SHGeoType.msh, SHGeoType.dmsh, ):
            header = "#   DETECTOR OUTPUT MSH/DMSH\n"
        elif det.geotyp == SHGeoType.geomap:
            header = "#   DETECTOR OUTPUT GEOMAP\n"
        else:
            header = "#   DETECTOR OUTPUT\n"

        # next block - scoring object geometrical information
        if det.geotyp in (SHGeoType.plane, SHGeoType.dplane, ):
            header += "#   PLANE point(X,Y,Z)         :"
            header += "{:s}".format(format_d(10, 3, det.xmin))
            header += "{:s}".format(format_d(10, 3, det.ymin))
            header += "{:s}\n".format(format_d(10, 3, det.zmin))
            header += "#   PLANE normal vect(Vx,Vy,Vz):"
            header += "{:s}".format(format_d(10, 3, det.xmax))
            header += "{:s}".format(format_d(10, 3, det.ymax))
            header += "{:s}\n".format(format_d(10, 3, det.zmax))
        elif det.geotyp in (SHGeoType.zone, SHGeoType.dzone, ):
            header += "#   ZONE START:{:6d} ZONE END:{:6d}\n".format(int(det.xmin), int(det.xmax))
        else:
            ax = self._axis_name(det.geotyp, 0)
            ay = self._axis_name(det.geotyp, 1)
            az = self._axis_name(det.geotyp, 2)
            header += "#   {:s} BIN:{:6d} {:s} BIN:{:6d} {:s} BIN:{:6d}\n".format(ax, det.nx, ay, det.ny, az, det.nz)

        # scored value and optionally particle type
        if det.geotyp != SHGeoType.geomap:
            header += "#   JPART:{:6d} DETECTOR TYPE: {:s}\n".format(det.particle, str(det.dettyp).ljust(10))
        else:
            det_type_name = str(det.dettyp)
            if det.dettyp in (SHDetType.zone, SHDetType.medium, ):
                det_type_name += "#"
            header += "#                DETECTOR TYPE: {:s}\n".format(str(det_type_name).ljust(10))

        # number of bins in each dimensions
        if det.geotyp not in (SHGeoType.plane, SHGeoType.dplane, SHGeoType.zone, SHGeoType.dzone):
            header += "#   {:s} START:{:s}".format(ax, format_d(10, 3, det.xmin))
            header += " {:s} START:{:s}".format(ay, format_d(10, 3, det.ymin))
            header += " {:s} START:{:s}\n".format(az, format_d(10, 3, det.zmin))
            header += "#   {:s} END  :{:s}".format(ax, format_d(10, 3, det.xmax))
            header += " {:s} END  :{:s}".format(ay, format_d(10, 3, det.ymax))
            header += " {:s} END  :{:s}\n".format(az, format_d(10, 3, det.zmax))

        # number of primaries
        header += "#   PRIMARIES:" + format_d(10, 3, det.nstat) + "\n"

        # due to some bug in original bdo2txt converter, no header is generated for cylindrical mesh
        if det.geotyp in (SHGeoType.cyl, SHGeoType.dcyl, ):
            header = ""

        # dump data
        with open(self.filename, 'w') as fout:
            logger.info("Writing: " + self.filename)
            fout.write(header)
            for x, y, z, v in zip(det.x, det.y, det.z, det.data):
                if det.geotyp in (SHGeoType.zone, SHGeoType.dzone):
                    x = 0.0
                else:
                    x = float('nan') if np.isnan(x) else x
                y = float('nan') if np.isnan(y) else y
                z = float('nan') if np.isnan(z) else z
                v = float('nan') if np.isnan(v) else v
                tmp = format_e(14, 7, x) + " " + \
                    format_e(14, 7, y) + " " + \
                    format_e(14, 7, z) + " " + \
                    format_e(23, 16, v) + "\n"
                fout.write(tmp)
