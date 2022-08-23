import logging
import os

import numpy as np

from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

logger = logging.getLogger(__name__)


class SHBinaryWriter:
    def __init__(self, filename, options):
        self.filename = filename

    def write(self, estimator):
        # TODO
        pass


class TxtWriter:
    @staticmethod
    def _axis_name(geo_type, axis_no):
        cyl = ('R', 'PHI', 'Z')
        msh = ('X', 'Y', 'Z')
        if geo_type in (SHGeoType.cyl, SHGeoType.dcyl):
            return cyl[axis_no]
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
    def _header_first_line(estimator):
        """first line with estimator geo type"""
        result = "#   DETECTOR OUTPUT\n"
        if estimator.geotyp in (SHGeoType.plane, SHGeoType.dplane,):
            result = "#             DETECTOR OUTPUT PLANE/DPLANE\n"
        elif estimator.geotyp in (SHGeoType.zone, SHGeoType.dzone,):
            result = "#             DETECTOR OUTPUT ZONE/DZONE\n"
        elif estimator.geotyp in (SHGeoType.msh, SHGeoType.dmsh,):
            result = "#   DETECTOR OUTPUT MSH/DMSH\n"
        elif estimator.geotyp == SHGeoType.geomap:
            result = "#   DETECTOR OUTPUT GEOMAP\n"
        return result

    def _header_geometric_info(self, det):
        """next block - scoring object geometrical information"""

        from pymchelper.writers.fortranformatter import format_d
        result = ""
        if det.geotyp in {SHGeoType.plane, SHGeoType.dplane}:
            result += "#   PLANE point(X,Y,Z)         :"
            result += f"{format_d(10, 3, det.sx)}{format_d(10, 3, det.sy)}{format_d(10, 3, det.sz)}\n"
            result += "#   PLANE normal vect(Vx,Vy,Vz):"
            result += f"{format_d(10, 3, det.nx)}{format_d(10, 3, det.ny)}{format_d(10, 3, det.nz)}\n"
        elif det.geotyp in {SHGeoType.zone, SHGeoType.dzone}:
            result += f"#   ZONE START:{int(det.x.min_val):6d} ZONE END:{int(det.x.max_val):6d}\n"
        else:
            result += f"#   {self.ax} BIN:{det.x.n:6d} {self.ay} BIN:{det.y.n:6d} {self.az} BIN:{det.z.n:6d}\n"
        return result

    @staticmethod
    def _header_scored_value(geotyp, dettyp, particle):
        """scored value and optionally particle type"""
        result = ""
        if geotyp != SHGeoType.geomap and particle:
            result += f"#   JPART:{particle:6d} DETECTOR TYPE: {str(dettyp).ljust(10)}\n"
        else:
            det_type_name = str(dettyp)
            if dettyp in (SHDetType.zone, SHDetType.medium,):
                det_type_name += "#"
            result += f"#                DETECTOR TYPE: {str(det_type_name).ljust(10)}\n"
        return result

    def _header_no_of_bins_and_prim(self, estimator):
        from pymchelper.writers.fortranformatter import format_d

        header = ""
        # number of bins in each dimensions
        if estimator.geotyp not in (SHGeoType.plane, SHGeoType.dplane, SHGeoType.zone, SHGeoType.dzone):
            header += f"#   {self.ax} START:{format_d(10, 3, estimator.x.min_val)}"
            header += f" {self.ay} START:{format_d(10, 3, estimator.y.min_val)}"
            header += f" {self.az} START:{format_d(10, 3, estimator.z.min_val)}\n"
            header += f"#   {self.ax} END  :{format_d(10, 3, estimator.x.max_val)}"
            header += f" {self.ay} END  :{format_d(10, 3, estimator.y.max_val)}"
            header += f" {self.az} END  :{format_d(10, 3, estimator.z.max_val)}\n"

        # number of primaries
        header += f"#   PRIMARIES:{format_d(10, 3, estimator.number_of_primaries)}\n"

        return header

    def write(self, estimator):
        """TODO"""
        # save to single page to a file without number (i.e. output.dat)
        if len(estimator.pages) == 1:
            self.write_single_page(estimator.pages[0], self.filename)
        else:
            # split output path into directory, basename and extension
            dir_path = os.path.dirname(self.filename)
            if not os.path.exists(dir_path):
                logger.info("Creating: %s", dir_path)
                os.makedirs(dir_path)
            file_base_part, file_ext = os.path.splitext(os.path.basename(self.filename))

            # loop over all pages and save an image for each of them
            for i, page in enumerate(estimator.pages):

                # calculate output filename. it will include page number padded with zeros.
                # for 10-99 pages the filename would look like: output_p01.png, ... output_p99.png
                # for 100-999 pages the filename would look like: output_p001.png, ... output_p999.png
                zero_padded_page_no = str(i + 1).zfill(len(str(len(estimator.pages))))
                output_filename = f"{file_base_part}_p{zero_padded_page_no}{file_ext}"
                output_path = os.path.join(dir_path, output_filename)

                # save the output file
                logger.info("Writing: %s", output_path)
                self.write_single_page(page, output_path)

        return 0

    def write_single_page(self, page, filename):
        """TODO"""
        logger.info("Writing: %s", filename)

        from pymchelper.writers.fortranformatter import format_e

        self.ax = self._axis_name(page.estimator.geotyp, 0)
        self.ay = self._axis_name(page.estimator.geotyp, 1)
        self.az = self._axis_name(page.estimator.geotyp, 2)

        # original bdo2txt is not saving header data for some of cylindrical scorers, hence we do the same
        if page.estimator.geotyp in (SHGeoType.cyl, SHGeoType.dcyl,) and \
                page.dettyp in (SHDetType.fluence, SHDetType.avg_energy, SHDetType.avg_beta, SHDetType.energy):
            header = ""
        else:
            header = self._header_first_line(page.estimator)

            header += self._header_geometric_info(page.estimator)

            header += self._header_scored_value(
                page.estimator.geotyp, page.dettyp, getattr(page.estimator, 'particle', None))

            header += self._header_no_of_bins_and_prim(page.estimator)

        # dump data
        with open(filename, 'w') as fout:  # skipcq: PTC-W6004
            logger.info("Writing: %s", filename)
            fout.write(header)

            det_error = page.error_raw.ravel()
            if np.all(np.isnan(page.error_raw)):
                det_error = [None] * page.data_raw.size
            xmesh = page.axis(0)
            ymesh = page.axis(1)
            zmesh = page.axis(2)

            logger.debug('xmesh %s', str(xmesh))
            logger.debug('ymesh %s', str(ymesh))
            logger.debug('zmesh %s', str(zmesh))

            zlist, ylist, xlist = np.meshgrid(zmesh.data, ymesh.data, xmesh.data, indexing='ij')

            logger.debug('xlist %s', str(xlist))
            logger.debug('ylist %s', str(ylist))
            logger.debug('zlist %s', str(zlist))

            for x, y, z, v, e in zip(xlist.ravel(), ylist.ravel(), zlist.ravel(), page.data.ravel(), det_error):
                if page.estimator.geotyp in {SHGeoType.zone, SHGeoType.dzone}:
                    x = 0.0
                # dirty hack to be compliant with old bdo2txt and files generated in old (<0.6) BDO format
                # this hack will be removed at some point together with bdo-style converter
                elif not hasattr(page.estimator, "mc_code_version") and page.estimator.geotyp == SHGeoType.plane:
                    x = (page.estimator.sx + page.estimator.nx) / 2.0
                    y = (page.estimator.sy + page.estimator.ny) / 2.0
                    z = (page.estimator.sz + page.estimator.nz) / 2.0
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
