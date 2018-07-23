import logging

import numpy as np

from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

logger = logging.getLogger(__name__)


class SHBinaryWriter:
    def __init__(self, filename, options):
        self.filename = filename

    def write(self, detector):
        # TODO
        pass


class TxtWriter:
    @staticmethod
    def _axis_name(geo_type, axis_no):
        cyl = ['R', 'PHI', 'Z']
        msh = ['X', 'Y', 'Z']
        if geo_type in (SHGeoType.cyl, SHGeoType.dcyl):
            return cyl[axis_no]
        else:
            return msh[axis_no]

    def __init__(self, filename, options):
        if filename.endswith(".txt"):
            self.filename = filename
        else:
            self.filename = filename + ".txt"
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
        if det.geotyp in {SHGeoType.plane, SHGeoType.dplane}:
            result += "#   PLANE point(X,Y,Z)         :"
            result += "{:s}".format(format_d(10, 3, det.sx))
            result += "{:s}".format(format_d(10, 3, det.sy))
            result += "{:s}\n".format(format_d(10, 3, det.sz))
            result += "#   PLANE normal vect(Vx,Vy,Vz):"
            result += "{:s}".format(format_d(10, 3, det.nx))
            result += "{:s}".format(format_d(10, 3, det.ny))
            result += "{:s}\n".format(format_d(10, 3, det.nz))
        elif det.geotyp in {SHGeoType.zone, SHGeoType.dzone}:
            result += "#   ZONE START:{:6d} ZONE END:{:6d}\n".format(int(det.x.min_val), int(det.x.max_val))
        else:
            result += "#   {:s} BIN:{:6d} {:s} BIN:{:6d} {:s} BIN:{:6d}\n".format(self.ax, det.x.n,
                                                                                  self.ay, det.y.n,
                                                                                  self.az, det.z.n)
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
            header += "#   {:s} START:{:s}".format(self.ax, format_d(10, 3, det.x.min_val))
            header += " {:s} START:{:s}".format(self.ay, format_d(10, 3, det.y.min_val))
            header += " {:s} START:{:s}\n".format(self.az, format_d(10, 3, det.z.min_val))
            header += "#   {:s} END  :{:s}".format(self.ax, format_d(10, 3, det.x.max_val))
            header += " {:s} END  :{:s}".format(self.ay, format_d(10, 3, det.y.max_val))
            header += " {:s} END  :{:s}\n".format(self.az, format_d(10, 3, det.z.max_val))

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

        # original bdo2txt is not saving header data for some of cylindrical scorers, hence we do the same
        if det.geotyp in (SHGeoType.cyl, SHGeoType.dcyl, ) and \
                det.dettyp in (SHDetType.fluence, SHDetType.avg_energy, SHDetType.avg_beta, SHDetType.energy):
            header = ""

        # dump data
        with open(self.filename, 'w') as fout:
            logger.info("Writing: " + self.filename)
            fout.write(header)

            det_error = det.error_raw.ravel()
            if np.all(np.isnan(det.error_raw)):
                det_error = [None] * det.data_raw.size
            zlist, ylist, xlist = np.meshgrid(det.z.data, det.y.data, det.x.data, indexing='ij')
            for x, y, z, v, e in zip(xlist.ravel(), ylist.ravel(), zlist.ravel(), det.data.ravel(), det_error):
                if det.geotyp in {SHGeoType.zone, SHGeoType.dzone}:
                    x = 0.0
                # dirty hack to be compliant with old bdo2txt and files generated in old (<0.6) BDO format
                # this hack will be removed at some point together with bdo-style converter
                elif not hasattr(det, "mc_code_version") and det.geotyp == SHGeoType.plane:
                    x = (det.sx + det.nx) / 2.0
                    y = (det.sy + det.ny) / 2.0
                    z = (det.sz + det.nz) / 2.0
                else:
                    x = float('nan') if np.isnan(x) else x
                y = float('nan') if np.isnan(y) else y
                z = float('nan') if np.isnan(z) else z
                v = float('nan') if np.isnan(v) else v
                tmp = format_e(14, 7, x) + " " + format_e(14, 7, y) + " " + \
                    format_e(14, 7, z) + " " + format_e(23, 16, v)

                if e is not None:
                    e = float('nan') if np.isnan(e) else e
                    tmp += " " + format_e(23, 16, e)

                tmp += "\n"

                fout.write(tmp)

        return 0
