from collections import namedtuple
import logging

import numpy as np

from pymchelper.axis import MeshAxis
from pymchelper.page import Page
from pymchelper.readers.shieldhit.reader_base import SHReader, mesh_unit_and_name, _bintyp, _get_detector_unit
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

logger = logging.getLogger(__name__)


class SHReaderBin2010(SHReader):
    """
    Binary format reader from 0.1 <= version <= 0.6
    """
    def read_header(self, estimator):
        logger.info("Reading header: " + self.filename)

        estimator.tripdose = 0.0
        estimator.tripntot = -1

        # effective read
        # first figure out if this is a VOXSCORE card
        header_dtype = np.dtype([('__fo1', '<i4'), ('geotyp', 'S10')])
        header = np.fromfile(self.filename, header_dtype, count=1)
        if not header:
            print("File {:s} has unknown format".format(self.filename))
            return None

        if 'VOXSCORE' in header['geotyp'][0].decode('ascii'):
            header_dtype = np.dtype([('__fo1', '<i4'),     # 0x00
                                     ('geotyp', 'S10'),    # 0x04
                                     ('__fo2', '<i4'),     # 0x0E
                                     ('__fo3', '<i4'),     # 0x12
                                     ('nstat', '<i4'),     # 0x16 : nstat
                                     ('__fo4', '<i4'),     # 0x1A
                                     ('__foo1', '<i4'),    # 0x1E
                                     ('tds', '<f4'),       # 0x22 : tripdose
                                     ('__foo2', '<i4'),    # 0x26
                                     ('__foo3', '<i4'),    # 0x2A
                                     ('tnt', '<i8'),       # 0x2E : tripntot
                                     ('__foo4', '<i4'),    # 0x36
                                     ('__fo5', '<i4'),     # 0x3A
                                     # DET has 8x float64
                                     ('det', ('<f8', 8)),  # 0x3E : DET
                                     ('__fo6', '<i4'),     # 0x7E
                                     ('__fo7', '<i4'),     # 0x82
                                     # IDET has 11x int32
                                     ('idet', '<i4', 11),  # 0x86 : IDET
                                     ('__fo8', '<i4'),     # 0xB2
                                     ('reclen', '<i4')])   # 0xB6
            # payload starts at 0xBA (186)
            estimator.payload_offset = 186
        else:
            # first figure out the length.
            header_dtype = np.dtype([('__fo1', '<i4'),
                                     ('geotyp', 'S10'),
                                     ('__fo2', '<i4'),
                                     ('__fo3', '<i4'),
                                     ('nstat', '<i4'),
                                     ('__fo4', '<i4'),
                                     ('__fo5', '<i4'),
                                     # DET has 8x float64
                                     ('det', ('<f8', 8)),  # DET
                                     ('__fo6', '<i4'),
                                     ('__fo7', '<i4'),
                                     # IDET has 11x int32
                                     ('idet', '<i4', 11),  # IDET
                                     ('__fo8', '<i4'),
                                     ('reclen', '<i4')])
            # payload starts at 0x9E (158)
            estimator.payload_offset = 158

        header = np.fromfile(self.filename, header_dtype, count=1)
        estimator.rec_size = header['reclen'][0] // 8

        if 'VOXSCORE' in header['geotyp'][0].decode('ascii'):
            estimator.tripdose = header['tds'][0]
            estimator.tripntot = header['tnt'][0]

        # map 10-elements table to namedtuple, for easier access
        # here is description of IDET table, assuming fortran-style numbering
        # (arrays starting from 1)
        # IDET(1) : Number of bins in first dimension. x or r or zones
        # IDET(2) : Number of bins in snd dimension, y or theta
        # IDET(3) : Number of bins in thrd dimension, z
        # IDET(4) : Particle type requested for scoring
        # IDET(5) : Detector type (see INITDET)
        # IDET(6) : Z of particle to be scored
        # IDET(7) : A of particle to be scored (only integers here)
        # IDET(8) : Detector material parameter
        # IDET(9) : Number of energy/amu (or LET) differential bins,
        #            negative if log.
        # IDET(10): Type of differential scoring, either LET, E/amu
        #            or polar angle
        # IDET(11): Starting zone of scoring for zone scoring
        DetectorAttributes = namedtuple('DetectorAttributes',
                                        ['dim_1_bins', 'dim_2_bins',
                                         'dim_3_bins',
                                         'particle_type', 'det_type',
                                         'particle_z', 'particle_a',
                                         'det_material',
                                         'diff_bins_no', 'diff_scoring_type',
                                         'starting_zone'])
        det_attribs = DetectorAttributes(*header['idet'][0])

        nx = det_attribs.dim_1_bins
        ny = det_attribs.dim_2_bins
        nz = det_attribs.dim_3_bins

        # DET(1-3): start positions for x y z or r theta z
        # DET(4-6): stop positions for x y z or r theta z
        # DET(7)  : start differential grid
        # DET(8)  : stop differential grid
        estimator.det = header['det']
        estimator.particle = det_attribs.particle_type

        try:
            estimator.geotyp = SHGeoType[header['geotyp'][0].decode('ascii').strip().lower()]
        except Exception:
            estimator.geotyp = SHGeoType.unknown
        estimator.number_of_primaries = header['nstat'][0]

        if estimator.geotyp not in {SHGeoType.zone, SHGeoType.dzone}:
            xmin = header['det'][0][0]
            ymin = header['det'][0][1]
            zmin = header['det'][0][2]

            xmax = header['det'][0][3]
            ymax = header['det'][0][4]
            zmax = header['det'][0][5]
        else:
            # special case for zone scoring, x min and max will be zone numbers
            xmin = det_attribs.starting_zone
            xmax = xmin + nx - 1
            ymin = 0.0
            ymax = 0.0
            zmin = 0.0
            zmax = 0.0

        if estimator.geotyp in {SHGeoType.plane, SHGeoType.dplane}:
            # special case for plane scoring, according to documentation we have:
            #  xmin, ymin, zmin = Sx, Sy, Sz (point on the plane)
            #  xmax, ymax, zmax = nx, ny, nz (normal vector)
            # to avoid situation where i.e. xmax < xmin (corresponds to nx < Sx)
            # we store only point on the plane
            estimator.sx, estimator.sy, estimator.sz = xmin, ymin, zmin
            estimator.nx, estimator.ny, estimator.nz = xmax, ymax, zmax
            xmax = xmin
            ymax = ymin
            zmax = zmin

        xunit, xname = mesh_unit_and_name(estimator, 0)
        yunit, yname = mesh_unit_and_name(estimator, 1)
        zunit, zname = mesh_unit_and_name(estimator, 2)

        estimator.x = MeshAxis(n=np.abs(nx), min_val=xmin, max_val=xmax, name=xname, unit=xunit, binning=_bintyp(nx))
        estimator.y = MeshAxis(n=np.abs(ny), min_val=ymin, max_val=ymax, name=yname, unit=yunit, binning=_bintyp(ny))
        estimator.z = MeshAxis(n=np.abs(nz), min_val=zmin, max_val=zmax, name=zname, unit=zunit, binning=_bintyp(nz))

        page = Page(estimator=estimator)
        page.dettyp = SHDetType(det_attribs.det_type)
        page.unit, page.name = _get_detector_unit(page.dettyp, estimator.geotyp)
        estimator.add_page(page)

        return True  # reading OK

    # TODO: we need an alternative list, in case things have been scaled with nscale, since then things
    # are not "/particle" anymore.
    def read_payload(self, estimator):
        logger.info("Reading data: " + self.filename)

        if estimator.geotyp == SHGeoType.unknown or estimator.pages[0].dettyp == SHDetType.none:
            logger.error("Unknown geotyp or dettyp")
            return None

        # next read the data:
        offset_str = "S" + str(estimator.payload_offset)
        record_dtype = np.dtype([('trash', offset_str),
                                 ('bin2', '<f8', estimator.rec_size)])
        record = np.fromfile(self.filename, record_dtype, count=-1)
        # BIN(*)  : a large array holding results. Accessed using pointers.
        estimator.pages[0].data_raw = np.array(record['bin2'][:][0])
        estimator.pages[0].error_raw = np.empty_like(estimator.pages[0].data_raw)

        logger.debug("Raw data: {}".format(estimator.pages[0].data_raw))

        estimator.file_counter = 1

        return True

    def read_data(self, estimator):
        if not self.read_header(estimator):
            logger.debug("Reading header failed")
            return None
        if not self.read_payload(estimator):
            logger.debug("Reading payload failed")
            return None
        estimator.file_format = 'bin2010'
        super(SHReaderBin2010, self).read_data(estimator)
        return True
