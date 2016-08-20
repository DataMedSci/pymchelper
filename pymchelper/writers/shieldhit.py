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
        self.ax = ''
        self.ay = ''
        self.az = ''

    @staticmethod
    def _header_first_line(det):
        """first line with detector geo type"""
        result = "#   DETECTOR OUTPUT\n"
        if det.geotyp in (SHGeoType.plane, SHGeoType.dplane, ):
            result = "#             DETECTOR OUTPUT PLANE/DPLANE\n"
        elif det.geotyp in (SHGeoType.zone, SHGeoType.dzone, ):
            result = "#             DETECTOR OUTPUT ZONE/DZONE\n"
        elif det.geotyp in (SHGeoType.msh, SHGeoType.dmsh, ):
            result = "#   DETECTOR OUTPUT MSH/DMSH\n"
        elif det.geotyp == SHGeoType.geomap:
            result = "#   DETECTOR OUTPUT GEOMAP\n"
        return result

    def _header_geometric_info(self, det):
        """next block - scoring object geometrical information"""

        from pymchelper.fortranformatter import format_d
        result = ""
        if det.geotyp in (SHGeoType.plane, SHGeoType.dplane, ):
            result += "#   PLANE point(X,Y,Z)         :"
            result += "{:s}".format(format_d(10, 3, det.xmin))
            result += "{:s}".format(format_d(10, 3, det.ymin))
            result += "{:s}\n".format(format_d(10, 3, det.zmin))
            result += "#   PLANE normal vect(Vx,Vy,Vz):"
            result += "{:s}".format(format_d(10, 3, det.xmax))
            result += "{:s}".format(format_d(10, 3, det.ymax))
            result += "{:s}\n".format(format_d(10, 3, det.zmax))
        elif det.geotyp in (SHGeoType.zone, SHGeoType.dzone, ):
            result += "#   ZONE START:{:6d} ZONE END:{:6d}\n".format(int(det.xmin), int(det.xmax))
        else:
            result += "#   {:s} BIN:{:6d} {:s} BIN:{:6d} {:s} BIN:{:6d}\n".format(self.ax, det.nx,
                                                                                  self.ay, det.ny,
                                                                                  self.az, det.nz)
        return result

    @staticmethod
    def _header_scored_value(det):
        """scored value and optionally particle type"""
        result = ""
        if det.geotyp != SHGeoType.geomap:
            result += "#   JPART:{:6d} DETECTOR TYPE: {:s}\n".format(det.particle, str(det.dettyp).ljust(10))
        else:
            det_type_name = str(det.dettyp)
            if det.dettyp in (SHDetType.zone, SHDetType.medium, ):
                det_type_name += "#"
            result += "#                DETECTOR TYPE: {:s}\n".format(str(det_type_name).ljust(10))
        return result

    def _header_no_of_bins_and_prim(self, det):
        from pymchelper.fortranformatter import format_d

        header = ""
        # number of bins in each dimensions
        if det.geotyp not in (SHGeoType.plane, SHGeoType.dplane, SHGeoType.zone, SHGeoType.dzone):
            header += "#   {:s} START:{:s}".format(self.ax, format_d(10, 3, det.xmin))
            header += " {:s} START:{:s}".format(self.ay, format_d(10, 3, det.ymin))
            header += " {:s} START:{:s}\n".format(self.az, format_d(10, 3, det.zmin))
            header += "#   {:s} END  :{:s}".format(self.ax, format_d(10, 3, det.xmax))
            header += " {:s} END  :{:s}".format(self.ay, format_d(10, 3, det.ymax))
            header += " {:s} END  :{:s}\n".format(self.az, format_d(10, 3, det.zmax))

        # number of primaries
        header += "#   PRIMARIES:" + format_d(10, 3, det.nstat) + "\n"

        return header

    def write(self, det):
        from pymchelper.fortranformatter import format_e

        self.ax = self._axis_name(det.geotyp, 0)
        self.ay = self._axis_name(det.geotyp, 1)
        self.az = self._axis_name(det.geotyp, 2)

        header = self._header_first_line(det)

        header += self._header_geometric_info(det)

        header += self._header_scored_value(det)

        header += self._header_no_of_bins_and_prim(det)

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
