import logging
import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from pymchelper.estimator import Estimator
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.writers.fortranformatter import format_e
from pymchelper.writers.writer import Writer

if TYPE_CHECKING:
    from pymchelper.page import Page

logger = logging.getLogger(__name__)


class SHBinaryWriter:

    def __init__(self, filename, options):
        self.filename = filename

    def write(self, estimator):
        # TODO
        pass


def _format_e_fast(w: int, d: int, val: float) -> str:
    """Same output as format_e(w, d, val), skipping its digit-by-digit composition for the common cases."""
    if val == 0.0:
        return f"0.{'0' * d}E+00".rjust(w)
    if math.isfinite(val):
        s = f"{abs(val):.{d - 1}e}"  # d.ddddddde+xx, correctly rounded as in format_e
        ex = int(s[d + 2:]) + 1
        if -99 <= ex <= 99:
            return f"{'-' if val < 0 else ''}0.{s[0]}{s[2:d + 1]}E{ex:+03d}".rjust(w)
    return format_e(w, d, val)


class TxtWriter(Writer):

    @staticmethod
    def _axis_name(geo_type: SHGeoType, axis_no: int) -> str:
        cyl = ('R', 'PHI', 'Z')
        msh = ('X', 'Y', 'Z')
        if geo_type in (SHGeoType.cyl, SHGeoType.dcyl):
            return cyl[axis_no]
        return msh[axis_no]

    def __init__(self, filename: str, options: object) -> None:
        super().__init__(filename if filename.endswith(".txt") else filename + ".txt")
        self.ax: str = ''
        self.ay: str = ''
        self.az: str = ''

    @staticmethod
    def _header_first_line(estimator: Estimator) -> str:
        """first line with estimator geo type"""
        result = "#   DETECTOR OUTPUT\n"
        if estimator.geotyp in (
                SHGeoType.plane,
                SHGeoType.dplane,
        ):
            result = "#             DETECTOR OUTPUT PLANE/DPLANE\n"
        elif estimator.geotyp in (
                SHGeoType.zone,
                SHGeoType.dzone,
        ):
            result = "#             DETECTOR OUTPUT ZONE/DZONE\n"
        elif estimator.geotyp in (
                SHGeoType.msh,
                SHGeoType.dmsh,
        ):
            result = "#   DETECTOR OUTPUT MSH/DMSH\n"
        elif estimator.geotyp == SHGeoType.geomap:
            result = "#   DETECTOR OUTPUT GEOMAP\n"
        return result

    def _header_geometric_info(self, det: Estimator) -> str:
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
    def _header_scored_value(geotyp: SHGeoType, dettyp: SHDetType, particle: object) -> str:
        """scored value and optionally particle type"""
        result = ""
        if geotyp != SHGeoType.geomap and particle:
            result += f"#   JPART:{particle:6d} DETECTOR TYPE: {str(dettyp).ljust(10)}\n"
        else:
            det_type_name = str(dettyp)
            if dettyp in (
                    SHDetType.zone,
                    SHDetType.medium,
            ):
                det_type_name += "#"
            result += f"#                DETECTOR TYPE: {str(det_type_name).ljust(10)}\n"
        return result

    def _header_no_of_bins_and_prim(self, estimator: Estimator) -> str:
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

    def write(self, estimator: Estimator) -> int:
        """TODO"""
        if estimator.file_format not in {'bdo2016', 'bdo2019'}:
            logger.error("Unsupported file format: %s", estimator.file_format)
            logger.error("This converter is designed for SHIELD-HIT12A output files only.")
            logger.error("Please use convertmc plotdata converter instead to generate text files.")
        return super().write(estimator)

    def write_single_page(self, page: 'Page', output_path: Path) -> None:
        """TODO"""
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

            header += self._header_scored_value(page.estimator.geotyp, page.dettyp,
                                                getattr(page.estimator, 'particle', None))

            header += self._header_no_of_bins_and_prim(page.estimator)

        # rows walk the bins with x fastest, page.data is indexed (x, y, z, diff1, diff2)
        zlist, ylist, xlist = np.meshgrid(page.axis(2).data, page.axis(1).data, page.axis(0).data, indexing='ij')
        xlist, ylist, zlist = xlist.ravel(), ylist.ravel(), zlist.ravel()
        if page.estimator.geotyp in {SHGeoType.zone, SHGeoType.dzone}:
            xlist = np.zeros_like(xlist)
        # dirty hack to be compliant with old bdo2txt and files generated in old (<0.6) BDO format
        # this hack will be removed at some point together with bdo-style converter
        elif not hasattr(page.estimator, "mc_code_version") and page.estimator.geotyp == SHGeoType.plane:
            xlist = np.full_like(xlist, (page.estimator.sx + page.estimator.nx) / 2.0)
            ylist = np.full_like(ylist, (page.estimator.sy + page.estimator.ny) / 2.0)
            zlist = np.full_like(zlist, (page.estimator.sz + page.estimator.nz) / 2.0)

        columns = [[_format_e_fast(14, 7, v) for v in col.tolist()] for col in (xlist, ylist, zlist)]
        columns.append([_format_e_fast(23, 16, v) for v in page.data.ravel(order='F').tolist()])
        if page.error is not None:
            columns.append([_format_e_fast(23, 16, v) for v in page.error.ravel(order='F').tolist()])

        logger.info("Writing: %s", output_path)
        with open(output_path, 'w') as fout:  # skipcq: PTC-W6004
            fout.write(header)
            fout.writelines(" ".join(row) + "\n" for row in zip(*columns))
