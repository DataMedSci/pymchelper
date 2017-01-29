import logging
from collections import namedtuple
from enum import IntEnum
import numpy as np
from distutils.version import LooseVersion

from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

logger = logging.getLogger(__name__)


def _prepare_detector_units(detector, nscale):
    """ Set units depending on detector type. Must be called by several classes.
    """

    # set units : detector.units are [x,y,z,v,data,detector_title]
    detector.units = [""] * 6
    detector.units[0:4] = SHBinaryReader.get_estimator_units(detector.geotyp)
    detector.units[4:6] = SHBinaryReader.get_detector_unit(detector.dettyp,
                                                           detector.geotyp)
    detector.title = detector.units[5]

    # dirty hack to change the units for differential scorers
    if hasattr(detector, 'dif_axis') and hasattr(detector, 'dif_type'):
        if detector.dif_type == 1:
            diff_unit = SHBinaryReader.get_detector_unit(SHDetType.energy, detector.geotyp)[0]
        elif detector.dif_type == 2:
            diff_unit = SHBinaryReader.get_detector_unit(SHDetType.let, detector.geotyp)[0]
        elif detector.dif_type == 3:
            diff_unit = SHBinaryReader.get_detector_unit(SHDetType.angle, detector.geotyp)[0]
        else:
            diff_unit = ""
        detector.units[detector.dif_axis] = diff_unit

    if detector.dimension == 0:
        detector.data = np.asarray([detector.data])

    if detector.geotyp == SHGeoType.plane:
        detector.data = np.asarray([detector.data])

    # normalize result if we need that.
    if detector.dettyp not in (SHDetType.dlet, SHDetType.tlet,
                               SHDetType.letflu,
                               SHDetType.dletg, SHDetType.tletg,
                               SHDetType.avg_energy, SHDetType.avg_beta,
                               SHDetType.material):
        if detector.nstat != 0:  # geotyp = GEOMAP will have 0 projectiles simulated
            detector.data /= np.float64(detector.nstat)

    if nscale != 1 and detector.dettyp in (SHDetType.energy, SHDetType.fluence, SHDetType.crossflu,
                                           SHDetType.dose, SHDetType.counter, SHDetType.pet):
        detector.data *= np.float64(nscale)  # scale with number of particles given by user
        if detector.dettyp == SHDetType.dose:
            detector.dettyp = SHDetType.dose_gy
        if detector.dettyp == SHDetType.alanine:
            detector.dettyp = SHDetType.alanine_gy
        if detector.dettyp in (SHDetType.dose_gy, SHDetType.alanine_gy):
            # 1 megaelectron volt / gram = 1.60217662 x 10-10 Gy
            detector.data *= np.float64(1.60217662e-10)
            detector.units[0:4] = SHBinaryReader.get_estimator_units(detector.geotyp)
            detector.units[4:6] = SHBinaryReader.get_detector_unit(detector.dettyp, detector.geotyp)
            detector.title = detector.units[5]


class SHBDOTagID(IntEnum):
    """ List of Tag ID numbers. Must be synchronized with sh_detect.h in SH12A.
    """

    # Hex values are used for better regognition in binary files, should they be inspected by humans.
    # Group 0x0000 - 0x00FF : Miscellaneous info
    shversion = 0x00    # [char*] full version string of shield-hit12a
    shbuilddate = 0x01  # [char*] date of build
    filedate = 0x02     # [char*] bdo file creation date, RFC 2822 compliant
    user = 0x03         # [char *] optional login name
    host = 0x04         # [char *] optional host where this file was created

    # Group 0xCC00 - 0xCCFF : Configuration
    dele = 0xCC00
    demin = 0xCC01
    itypst = 0xCC02
    itypms = 0xCC03
    oln = 0xCC04
    inucre = 0xCC05
    iemtrans = 0xCC06
    iextspec = 0xCC07
    intrfast = 0xCC08
    intrslow = 0xCC09
    apzlscl = 0xCC0A
    ioffset = 0xCC0B
    irifimc = 0xCC0C
    irifitrans = 0xCC0D
    irifizone = 0xCC0E
    ext_nproj = 0xCC0F
    ext_ptvdose = 0xCC10
    ixfirs = 0xCC11

    # Group 0xCE00 - 0xCEFF : CT specific tags
    ct_ang = 0xCE00   # holds two doubles with the couch and gantry angle
    ct_icnt = 0xCE01  # holds three
    ct_len = 0xCE02   # holds three

    # Group 0xEE00 - 0xEEFF : Estimator specific tags
    # estimator specific tags
    est_geotyp = 0xEE00    # may differ from det_geotyp in case of spc
    est_pages = 0xEE01     # number of detectors / pages for this estimator

    # Group 0xDD00 - 0xDDFF : Detector/page specific tags
    det_geotyp = 0xDD00      # may differ from est_geotyp in case of spc
    det_nbin = 0xDD01        # idet(1-3) (len=3) number of bins x,y,z
    det_part = 0xDD02        # idet(4) particle type which was scored
    det_dtype = 0xDD03       # idet(5) detector type
    det_partz = 0xDD04       # idet(6)
    det_parta = 0xDD05       # idet(7)
    det_dmat = 0xDD06        # idet(8)
    det_nbine = 0xDD07       # idet(9) number of bins in diff scorer, negative means log binning
    det_difftype = 0xDD08    # idet(10) detector type for differential scorer (i.e. angle, energy, let)
    det_zonestart = 0xDD09   # idet(11)
    det_dsize = 0xDD0A       # idet(12)
    det_dsizexyz = 0xDD0B    # idet(13)

    det_xyz_start = 0xDD0C   # det(1-3)
    det_xyz_stop = 0xDD0D    # det(4-6)
    det_dif_start = 0xDD0E   # det(7)
    det_dif_stop = 0xDD0F    # det(8)
    det_voxvol = 0xDD10      # det(9)

    det_data = 0xDDBB        # data block

    # Group 0xAA00 - 0xAAFF : Runtime variables
    rt_nstat = 0xAA00        # number of actually simulated particles
    rt_time = 0xAA01         # [usignend long int] optional runtime in seconds


# for future use
# mapping = {SHBDOTagID.shversion: "mc_code_version",
#           SHBDOTagID.filedate: "filedate",
#           SHBDOTagID.user: "user",
#           SHBDOTagID.host: "host",
#           SHBDOTagID.rt_nstat: "nstat",
#           SHBDOTagID.det_dtype: "dettyp",
#           SHBDOTagID.est_geotyp: "geotyp",
#           SHBDOTagID.det_xyz_start: ("xmin", "ymin", "zmin"),
#           SHBDOTagID.det_xyz_stop: ("xmax", "ymax", "zmax"),
#           SHBDOTagID.det_nbin: ("nx", "ny", "nz")}


class SHBinaryReader:
    """
    Reads binary output files generated by SHIELD-HIT12A code.
    """
    def __init__(self, filename):
        self.filename = filename

    def test_version_0p6(self):
        sh_bdo_magic_number = b'xSH12A'
        with open(self.filename, "rb") as f:
            d1 = np.dtype([('magic', 'S6'),
                           ('end', 'S2'),
                           ('vstr', 'S16')])
            x = np.fromfile(f, dtype=d1, count=1)

            # if magic string is present, deep check for version number
            if sh_bdo_magic_number == x['magic'][0]:
                ver = x['vstr'][0].decode('ASCII')
                return (sh_bdo_magic_number == x['magic'][0]) and (LooseVersion(ver) >= LooseVersion("0.6"))
            else:
                return False

    def read(self, detector, nscale=1):
        if self.test_version_0p6():
            reader = _SHBinaryReader0p6(self.filename)
            reader.read(detector, nscale)
        else:
            reader = _SHBinaryReader0p1(self.filename)
            reader.read_header(detector)
            reader.read_payload(detector, nscale)

    @staticmethod
    def get_estimator_units(geotyp):
        """
        TODO
        :param geotyp:
        :return:
        """
        _geotyp_units = {
            SHGeoType.msh: ("cm", "cm", "cm", "(nil)"),
            SHGeoType.dmsh: ("cm", "cm", "cm", "(nil)"),
            SHGeoType.cyl: ("cm", "radians", "cm", "(nil)"),
            SHGeoType.dcyl: ("cm", "radians", "cm", "(nil)"),
            SHGeoType.zone: ("zone number", "(nil)", "(nil)", "(nil)"),
            SHGeoType.voxscore: ("cm", "cm", "cm", "(nil)"),
            SHGeoType.geomap: ("cm", "cm", "cm", "(nil)"),
            SHGeoType.plane: ("cm", "cm", "cm", "(nil)"),  # TODO fix me later
        }
        _default_units = ("(nil)", "(nil)", "(nil)", "(nil)")
        return _geotyp_units.get(geotyp, _default_units)

    @staticmethod
    def get_detector_unit(detector_type, geotyp):
        """
        TODO
        :param detector_type:
        :param geotyp:
        :return:
        """
        if geotyp == SHGeoType.zone:
            dose_units = ("MeV/primary", "Dose*volume")
            dose_gy_units = ("J", "Dose*volume")
            alanine_units = ("MeV/primary", "Alanine RE*Dose*volume")
            alanine_gy_units = ("J", "Alanine RE*Dose*volume")
        else:
            dose_units = (" MeV/g/primary", "Dose")
            dose_gy_units = ("Gy", "Dose")
            alanine_units = ("MeV/g/primary", "Alanine RE*Dose")
            alanine_gy_units = ("Gy", "Alanine RE*Dose")

        _detector_units = {
            SHDetType.unknown: ("(nil)", "None"),
            SHDetType.energy: ("MeV/primary", "Energy"),
            SHDetType.fluence: (" cm^-2/primary", "Fluence"),
            SHDetType.crossflu: (" cm^-2/primary", "Planar fluence"),
            SHDetType.letflu: (" MeV/cm", "LET fluence"),
            SHDetType.dose: dose_units,
            SHDetType.dose_gy: dose_gy_units,
            SHDetType.dlet: ("keV/um", "dose-averaged LET"),
            SHDetType.tlet: ("keV/um", "track-averaged LET"),
            SHDetType.avg_energy: ("MeV", "Average energy"),
            SHDetType.avg_beta: ("(dimensionless)", "Average beta"),
            SHDetType.material: ("(nil)", "Material number"),
            SHDetType.alanine: alanine_units,
            SHDetType.alanine_gy: alanine_gy_units,
            SHDetType.counter: ("/primary", "Particle counter"),
            SHDetType.pet: ("/primary", "PET isotopes"),
            SHDetType.dletg: ("keV/um", "dose-averaged LET"),
            SHDetType.tletg: ("keV/um", "track-averaged LET"),
            SHDetType.zone: ("(dimensionless)", "Zone#"),
            SHDetType.medium: ("(dimensionless)", "Medium#"),
            SHDetType.rho: ("g/cm^3", "Density"),
            SHDetType.angle: ("radians", "Angle")
        }
        return _detector_units.get(detector_type, ("(nil)", "(nil)"))


class _SHBinaryReader0p6:
    """
    Binary format reader from version >= 0.6
    """
    def __init__(self, filename):
        self.filename = filename

    def read(self, detector, nscale=1):
        logger.info("Reading: " + self.filename)
        with open(self.filename, "rb") as f:
            d1 = np.dtype([('magic', 'S6'),
                           ('end', 'S2'),
                           ('vstr', 'S16')])

            _x = np.fromfile(f, dtype=d1, count=1)  # read the data into numpy
            logger.debug("Magic : " + _x['magic'][0].decode('ASCII'))
            logger.debug("Endian: " + _x['end'][0].decode('ASCII'))
            logger.debug("VerStr: " + _x['vstr'][0].decode('ASCII'))

            while f:
                token = self.get_token(f)
                if token is None:
                    break

                pl_id, _pl_type, _pl_len, _pl = token

                pl = [None]*_pl_len

                # decode all strings (currently there will never be more than one per token)
                if 'S' in _pl_type.decode('ASCII'):
                    for i, _j in enumerate(_pl):
                        pl[i] = _pl[i].decode('ASCII').strip()
                else:
                    pl = _pl

                logger.debug("Read token {:s} 0x{:02x}".format(_pl_type.decode('ASCII'), pl_id))

                # TODO: some clever mapping could be done here surely
                # something like this: however the keymaps are not complete
                # attr_keys = SHBDOTagID(pl_id)
                # attributes = mapping[attr_keys]
                # for i, attr in enumerate(attributes):
                #     setattr(detector,attr,pl[i])
                #

                if pl_id == SHBDOTagID.shversion:
                    detector.mc_code_version = pl[0]
                    logger.debug("MC code version:" + detector.mc_code_version)

                if pl_id == SHBDOTagID.filedate:
                    detector.filedate = pl[0]

                if pl_id == SHBDOTagID.user:
                    detector.user = pl[0]

                if pl_id == SHBDOTagID.host:
                    detector.host = pl[0]

                if pl_id == SHBDOTagID.rt_nstat:
                    detector.nstat = pl[0]

                    # estimator block here ---
                if pl_id == SHBDOTagID.est_geotyp:
                    detector.geotyp = SHGeoType[pl[0].strip().lower()]

                if pl_id == SHBDOTagID.ext_ptvdose:
                    detector.tripdose = 0.0

                if pl_id == SHBDOTagID.ext_nproj:
                    detector.tripntot = -1

                if pl_id == SHBDOTagID.est_pages:
                    detector.pages = pl[0]
                    # todo: handling of multiple detectors (SPC)

                # read a single detector
                if pl_id == SHBDOTagID.det_dtype:
                    detector.dettyp = SHDetType(pl[0])

                if pl_id == SHBDOTagID.det_part:  # particle to be scored
                    detector.particle = pl[0]
                if pl_id == SHBDOTagID.det_partz:  # particle to be scored
                    detector.particle_z = pl[0]
                if pl_id == SHBDOTagID.det_parta:  # particle to be scored
                    detector.particle_a = pl[0]

                if pl_id == SHBDOTagID.det_nbin:
                    detector.nx = pl[0]
                    detector.ny = pl[1]
                    detector.nz = pl[2]

                if pl_id == SHBDOTagID.det_xyz_start:
                    detector.xmin = pl[0]
                    detector.ymin = pl[1]
                    detector.zmin = pl[2]

                if pl_id == SHBDOTagID.det_xyz_stop:
                    detector.xmax = pl[0]
                    detector.ymax = pl[1]
                    detector.zmax = pl[2]

                # partial support for differential scoring (only linear binning)
                # TODO add some support for DMSH, DCYL and DZONE
                # TODO add support for logarithmic binning
                if detector.geotyp in (SHGeoType.dplane, SHGeoType.dmsh, SHGeoType.dcyl, SHGeoType.dzone):
                    if pl_id == SHBDOTagID.det_dif_start:
                        detector.dif_min = pl[0]

                    if pl_id == SHBDOTagID.det_dif_stop:
                        detector.dif_max = pl[0]

                    if pl_id == SHBDOTagID.det_nbine:
                        detector.dif_n = pl[0]

                    if pl_id == SHBDOTagID.det_difftype:
                        detector.dif_type = pl[0]

                if pl_id == SHBDOTagID.det_data:
                    detector.data = np.asarray(pl)

            # differential scoring data replacement
            if hasattr(detector, 'dif_min') and hasattr(detector, 'dif_max') and hasattr(detector, 'dif_n'):
                if detector.nz == 1:
                    detector.nz = detector.dif_n
                    detector.zmin = detector.dif_min
                    detector.zmax = detector.dif_max
                    detector.dif_axis = 2
                elif detector.ny == 1:
                    detector.ny = detector.dif_n
                    detector.ymin = detector.dif_min
                    detector.ymax = detector.dif_max
                    detector.dif_axis = 1
                elif detector.nx == 1:
                    detector.nx = detector.dif_n
                    detector.xmin = detector.dif_min
                    detector.xmax = detector.dif_max
                    detector.dif_axis = 0

            logger.debug("Done reading bdo file.")
            logger.debug("Detector data : " + str(detector.data))
            logger.debug("Detector nstat: " + str(detector.nstat))
            logger.debug("Detector nx   : " + str(detector.nx))
            logger.debug("Detector ny   : " + str(detector.ny))
            logger.debug("Detector nz   : " + str(detector.nz))
            _prepare_detector_units(detector, nscale)
            detector.counter = 1

    def get_token(self, f):
        """
        returns a tuple with 4 elements:
        0: payload id
        1: payload dtype string
        2: payload number of elements
        3: payload itself
        f is an open and readable file pointer.
        returns None if no token was found / EOF
        """

        tag = np.dtype([('pl_id', '<u8'),
                        ('pl_type', 'S8'),
                        ('pl_len', '<u8')])

        x1 = np.fromfile(f, dtype=tag, count=1)  # read the data into numpy

        if not x1:
            return None
        else:
            pl_id = x1['pl_id'][0]
            pl_type = x1['pl_type'][0]
            pl_len = x1['pl_len'][0]
            pl = np.fromfile(f,
                             dtype=pl_type,
                             count=pl_len)  # read the data into numpy
            return(pl_id, pl_type, pl_len, pl)


class _SHBinaryReader0p1:
    """
    Binary format reader from 0.1 <= version <= 0.6
    """
    def __init__(self, filename):
        self.filename = filename

    def read_header(self, detector):
        logger.info("Reading header: " + self.filename)

        detector.tripdose = 0.0
        detector.tripntot = -1

        # effective read
        # first figure out if this is a VOXSCORE card
        header_dtype = np.dtype([('__fo1', '<i4'), ('geotyp', 'S10')])
        header = np.fromfile(self.filename, header_dtype, count=1)

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
            detector.payload_offset = 186
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
            detector.payload_offset = 158

        header = np.fromfile(self.filename, header_dtype, count=1)
        detector.rec_size = header['reclen'][0] // 8

        if 'VOXSCORE' in header['geotyp'][0].decode('ascii'):
            detector.tripdose = header['tds'][0]
            detector.tripntot = header['tnt'][0]

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

        detector.nx = det_attribs.dim_1_bins
        detector.ny = det_attribs.dim_2_bins
        detector.nz = det_attribs.dim_3_bins

        # DET(1-3): start positions for x y z or r theta z
        # DET(4-6): stop positions for x y z or r theta z
        # DET(7)  : start differential grid
        # DET(8)  : stop differential grid
        detector.det = header['det']
        detector.particle = det_attribs.particle_type

        try:
            detector.geotyp = SHGeoType[header['geotyp'][0].decode('ascii').strip().lower()]
        except Exception:
            detector.geotyp = SHGeoType.unknown
        detector.nstat = header['nstat'][0]

        if detector.geotyp not in (SHGeoType.zone, SHGeoType.dzone):
            detector.xmin = header['det'][0][0]
            detector.ymin = header['det'][0][1]
            detector.zmin = header['det'][0][2]

            detector.xmax = header['det'][0][3]
            detector.ymax = header['det'][0][4]
            detector.zmax = header['det'][0][5]
        else:
            # special case for zone scoring, x min and max will be zone numbers
            detector.xmin = det_attribs.starting_zone
            detector.xmax = detector.xmin + detector.nx - 1
            detector.ymin = 0.0
            detector.ymax = 0.0
            detector.zmin = 0.0
            detector.zmax = 0.0

        detector.dettyp = SHDetType(det_attribs.det_type)

    # TODO: we need an alternative list, in case things have been scaled with nscale, since then things
    # are not "/particle" anymore.
    def read_payload(self, detector, nscale=1):
        logger.info("Reading data: " + self.filename)

        if detector.geotyp == SHGeoType.unknown or detector.dettyp == SHDetType.unknown:
            detector.data = []
            return

        # next read the data:
        offset_str = "S" + str(detector.payload_offset)
        record_dtype = np.dtype([('trash', offset_str),
                                 ('bin2', '<f8', detector.rec_size)])
        record = np.fromfile(self.filename, record_dtype, count=-1)
        # BIN(*)  : a large array holding results. Accessed using pointers.
        detector.data = record['bin2'][:][0]

        _prepare_detector_units(detector, nscale)
        detector.counter = 1

    def read(self, detector, nscale=1):
        self.read_header(detector)
        self.read_payload(detector, nscale)


class SHTextReader:
    """
    Reads plain text files with data saved by binary-to-ascii converter.
    """
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
