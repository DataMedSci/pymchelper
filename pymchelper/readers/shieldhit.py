import logging
from collections import namedtuple
from enum import IntEnum
import numpy as np
from distutils.version import LooseVersion

from pymchelper.detector import MeshAxis
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

logger = logging.getLogger(__name__)


def _get_mesh_units(detector, axis):
    """ Set units depending on detector type.
    """

    _geotyp_units = {
        SHGeoType.msh: ("cm", "cm", "cm"),
        SHGeoType.dmsh: ("cm", "cm", "cm"),
        SHGeoType.cyl: ("cm", "radians", "cm"),
        SHGeoType.dcyl: ("cm", "radians", "cm"),
        SHGeoType.zone: ("zone number", "(nil)", "(nil)"),
        SHGeoType.voxscore: ("cm", "cm", "cm"),
        SHGeoType.geomap: ("cm", "cm", "cm"),
        SHGeoType.plane: ("cm", "cm", "cm"),
        SHGeoType.dplane: ("cm", "cm", "cm")
    }
    _default_units = ("(nil)", "(nil)", "(nil)")

    unit = _geotyp_units.get(detector.geotyp, _default_units)[axis]

    if detector.geotyp in {SHGeoType.msh, SHGeoType.dmsh, SHGeoType.voxscore, SHGeoType.geomap,
                           SHGeoType.plane, SHGeoType.dplane}:
        name = ("Position (X)", "Position (Y)", "Position (Z)")[axis]
    elif detector.geotyp in {SHGeoType.cyl, SHGeoType.dcyl}:
        name = ("Radius (R)", "Angle (PHI)", "Position (Z)")[axis]
    else:
        name = ""

    # dirty hack to change the units for differential scorers
    if hasattr(detector, 'dif_axis') and hasattr(detector, 'dif_type') and axis == detector.dif_axis:
        if detector.dif_type == 1:
            unit, name = _get_detector_unit(SHDetType.energy, detector.geotyp)
        elif detector.dif_type == 2:
            unit, name = _get_detector_unit(SHDetType.let, detector.geotyp)
        elif detector.dif_type == 3:
            unit, name = _get_detector_unit(SHDetType.angle, detector.geotyp)
        else:
            unit, name = "", ""

    return unit, name


def _get_detector_unit(detector_type, geotyp):
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
        SHDetType.fluence: ("cm^-2/primary", "Fluence"),
        SHDetType.crossflu: ("cm^-2/primary", "Planar fluence"),
        SHDetType.letflu: ("MeV/cm", "LET fluence"),
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
        SHDetType.q: ("(nil)", "beam quality Q"),
        SHDetType.flu_char: ("cm^-2/primary", "Charged particle fluence"),
        SHDetType.flu_neut: ("cm^-2/primary", "Neutral particle fluence"),
        SHDetType.let: ("keV/um", "LET"),
        SHDetType.angle: ("radians", "Angle"),
        SHDetType.zone: ("(dimensionless)", "Zone#"),
        SHDetType.medium: ("(dimensionless)", "Medium#"),
        SHDetType.rho: ("g/cm^3", "Density")
    }
    return _detector_units.get(detector_type, ("(nil)", "(nil)"))


def _postprocess(detector, nscale):
    """normalize result if we need that."""
    if detector.dettyp not in (SHDetType.dlet, SHDetType.tlet,
                               SHDetType.letflu,
                               SHDetType.dletg, SHDetType.tletg,
                               SHDetType.avg_energy, SHDetType.avg_beta,
                               SHDetType.material,
                               SHDetType.q):
        if detector.nstat != 0:  # geotyp = GEOMAP will have 0 projectiles simulated
            detector.data_raw /= np.float64(detector.nstat)
            detector.error_raw /= np.float64(detector.nstat)

    if nscale != 1:
        # scale with number of particles given by user
        detector.data_raw *= np.float64(nscale)
        detector.error_raw *= np.float64(nscale)

        # rescaling with particle number means also unit change for some detectors
        # from per particle to Grey - this is why we override detector type
        if detector.dettyp == SHDetType.dose:
            detector.dettyp = SHDetType.dose_gy
        if detector.dettyp == SHDetType.alanine:
            detector.dettyp = SHDetType.alanine_gy
        # for the same reason as above we change units
        if detector.dettyp in (SHDetType.dose_gy, SHDetType.alanine_gy):
            # 1 megaelectron volt / gram = 1.60217662 x 10-10 Gy
            MeV_g = np.float64(1.60217662e-10)
            detector.data_raw *= MeV_g
            detector.error_raw *= MeV_g
            detector.unit, detector.name = _get_detector_unit(detector.dettyp, detector.geotyp)


class SHBDOTagID(IntEnum):
    """ List of Tag ID numbers. Must be synchronized with sh_detect.h in SH12A.
    """

    # Hex values are used for better recognition in binary files, should they be inspected by humans.
    # Group 0x0000 - 0x00FF : Miscellaneous info
    shversion = 0x00    # [char*] full version string of shield-hit12a
    shbuilddate = 0x01  # [char*] date of build
    filedate = 0x02     # [char*] bdo file creation date, RFC 2822 compliant
    user = 0x03         # [char *] optional login name
    host = 0x04         # [char *] optional host where this file was created

    # Group 0xCB00 - 0xCBFF : Beam configuration
    jpart0 = 0xCB00     # [int] primary particle id
    apro0 = 0xCB01      # [float] number of nucleons a of the beam particles.
    zpro0 = 0xCB02      # [float] charge z of the beam particles.
    beamx = 0xCB03      # [float] start position of the beam - x coordinate
    beamy = 0xCB04      # [float] start position of the beam - y coordinate
    beamz = 0xCB05      # [float] start position of the beam - z coordinate
    sigmax = 0xCB06     # [float] lateral extension of the beam in x direction
    sigmay = 0xCB07     # [float] lateral extension of the beam in y direction
    tmax0 = 0xCB08      # [float] the initial energy of the primary particle
    sigmat0 = 0xCB09    # [float] energy spread of the primary particle
    beamtheta = 0xCB0A  # [float] polar angle
    beamphi = 0xCB0B    # [float] azimuth angle
    beamdivx = 0xCB0C   # [float] beam divergence - x coordinate
    beamdivy = 0xCB0D   # [float] beam divergence - y coordinate
    beamdivk = 0xCB0E   # [float] beam divergence - focus

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
    det_thresh = 0xDD11       # det(10) lower energy scoring threshold

    det_data = 0xDDBB        # data block

    # Group 0xAA00 - 0xAAFF : Runtime variables
    rt_nstat = 0xAA00        # number of actually simulated particles
    rt_time = 0xAA01         # [unsigned long int] optional runtime in seconds


tag_to_name = {
    SHBDOTagID.jpart0: 'projectile_code',
    SHBDOTagID.apro0: 'projectile_a',
    SHBDOTagID.zpro0: 'projectile_z',
    SHBDOTagID.beamx: 'projectile_position_x',
    SHBDOTagID.beamy: 'projectile_position_y',
    SHBDOTagID.beamz: 'projectile_position_z',
    SHBDOTagID.sigmax: 'projectile_sigma_x',
    SHBDOTagID.sigmay: 'projectile_sigma_y',
    SHBDOTagID.tmax0: 'projectile_energy',
    SHBDOTagID.sigmat0: 'projectile_sigma_energy',
    SHBDOTagID.beamtheta: 'projectile_polar_angle',
    SHBDOTagID.beamphi: 'projectile_azimuth_angle',
    SHBDOTagID.beamdivx: 'projectile_divergence_x',
    SHBDOTagID.beamdivy: 'projectile_divergence_y',
    SHBDOTagID.beamdivk: 'projectile_divergence_k'
}


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
            reader.read(detector)
        else:
            reader = _SHBinaryReader0p1(self.filename)
            reader.read_header(detector)
            reader.read_payload(detector)
        _postprocess(detector, nscale)


def _bintyp(n):
    """
    Calculates type of binning based on number of bins.

    We follow the convention that positive number of bins means linear binning,
    while the negative - logarithmic.

    :param n: number of bins
    :return: MeshAxis.BinningType.linear or MeshAxis.BinningType.logarithmic
    """
    return MeshAxis.BinningType.linear if n > 0 else MeshAxis.BinningType.logarithmic


class _SHBinaryReader0p6:
    """
    Binary format reader from version >= 0.6
    """
    def __init__(self, filename):
        self.filename = filename

    def read(self, detector):
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

                pl = [None] * _pl_len

                # decode all strings (currently there will never be more than one per token)
                if 'S' in _pl_type.decode('ASCII'):
                    for i, _j in enumerate(_pl):
                        pl[i] = _pl[i].decode('ASCII').strip()
                else:
                    pl = _pl

                logger.debug("Read token {:s} 0x{:02x}".format(_pl_type.decode('ASCII'), pl_id))

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

                # beam configuration etc...
                if pl_id in tag_to_name:
                    setattr(detector, tag_to_name[pl_id], pl[0])

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
                    detector.scored_particle_code = pl[0]
                if pl_id == SHBDOTagID.det_partz:  # particle to be scored
                    detector.scored_particle_z = pl[0]
                if pl_id == SHBDOTagID.det_parta:  # particle to be scored
                    detector.scored_particle_a = pl[0]

                if pl_id == SHBDOTagID.det_nbin:
                    nx = pl[0]
                    ny = pl[1]
                    nz = pl[2]

                if pl_id == SHBDOTagID.det_xyz_start:
                    xmin = pl[0]
                    ymin = pl[1]
                    zmin = pl[2]

                if pl_id == SHBDOTagID.det_xyz_stop:
                    xmax = pl[0]
                    ymax = pl[1]
                    zmax = pl[2]

                # partial support for differential scoring (only linear binning)
                # TODO add some support for DMSH, DCYL and DZONE
                # TODO add support for logarithmic binning
                diff_geotypes = {SHGeoType.dplane, SHGeoType.dmsh, SHGeoType.dcyl, SHGeoType.dzone}
                if hasattr(detector, 'geotyp') and detector.geotyp in diff_geotypes:
                    if pl_id == SHBDOTagID.det_dif_start:
                        detector.dif_min = pl[0]

                    if pl_id == SHBDOTagID.det_dif_stop:
                        detector.dif_max = pl[0]

                    if pl_id == SHBDOTagID.det_nbine:
                        detector.dif_n = pl[0]

                    if pl_id == SHBDOTagID.det_difftype:
                        detector.dif_type = pl[0]

                if pl_id == SHBDOTagID.det_zonestart:
                    detector.zone_start = pl[0]

                if pl_id == SHBDOTagID.det_data:
                    detector.data_raw = np.asarray(pl)

            # TODO: would be better to not overwrite x,y,z and make proper case for ZONE scoring later.
            if detector.geotyp in {SHGeoType.zone, SHGeoType.dzone}:
                # special case for zone scoring, x min and max will be zone numbers
                xmin = detector.zone_start
                xmax = xmin + nx - 1
                ymin = 0.0
                ymax = 0.0
                zmin = 0.0
                zmax = 0.0
            elif detector.geotyp in {SHGeoType.plane, SHGeoType.dplane}:
                # special case for plane scoring, according to documentation we have:
                #  xmin, ymin, zmin = Sx, Sy, Sz (point on the plane)
                #  xmax, ymax, zmax = nx, ny, nz (normal vector)
                # to avoid situation where i.e. xmax < xmin (corresponds to nx < Sx)
                # we store only point on the plane
                detector.sx, detector.sy, detector.sz = xmin, ymin, zmin
                detector.nx, detector.ny, detector.nz = xmax, ymax, zmax
                xmax = xmin
                ymax = ymin
                zmax = zmin

            # check if scoring quantity is LET, if yes, than change units from [MeV/cm] to [keV/um]
            if hasattr(detector, 'dif_type') and detector.dif_type == 2:
                detector.dif_min /= 10.0
                detector.dif_max /= 10.0

            # # differential scoring data replacement
            if hasattr(detector, 'dif_min') and hasattr(detector, 'dif_max') and hasattr(detector, 'dif_n'):
                if nz == 1:
                    # max two axis (X or Y) filled with scored value, Z axis empty
                    # we can put differential quantity as Z axis
                    nz = detector.dif_n
                    zmin = detector.dif_min
                    zmax = detector.dif_max
                    detector.dif_axis = 2
                elif ny == 1:
                    # Z axis filled with scored value (X axis maybe also), Y axis empty
                    # we can put differential quantity as Y axis
                    ny = detector.dif_n
                    ymin = detector.dif_min
                    ymax = detector.dif_max
                    detector.dif_axis = 1
                elif nx == 1:
                    nx = detector.dif_n
                    xmin = detector.dif_min
                    xmax = detector.dif_max
                    detector.dif_axis = 0

            xunit, xname = _get_mesh_units(detector, 0)
            yunit, yname = _get_mesh_units(detector, 1)
            zunit, zname = _get_mesh_units(detector, 2)

            detector.x = MeshAxis(n=np.abs(nx), min_val=xmin, max_val=xmax, name=xname, unit=xunit, binning=_bintyp(nx))
            detector.y = MeshAxis(n=np.abs(ny), min_val=ymin, max_val=ymax, name=yname, unit=yunit, binning=_bintyp(ny))
            detector.z = MeshAxis(n=np.abs(nz), min_val=zmin, max_val=zmax, name=zname, unit=zunit, binning=_bintyp(nz))

            detector.unit, detector.name = _get_detector_unit(detector.dettyp, detector.geotyp)

            logger.debug("Done reading bdo file.")
            logger.debug("Detector data : " + str(detector.data))
            logger.debug("Detector nstat: " + str(detector.nstat))
            logger.debug("Detector nx   : " + str(detector.x.n))
            logger.debug("Detector ny   : " + str(detector.y.n))
            logger.debug("Detector nz   : " + str(detector.z.n))
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
            return (pl_id, pl_type, pl_len, pl)


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

        nx = det_attribs.dim_1_bins
        ny = det_attribs.dim_2_bins
        nz = det_attribs.dim_3_bins

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

        if detector.geotyp not in {SHGeoType.zone, SHGeoType.dzone}:
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

        if detector.geotyp in {SHGeoType.plane, SHGeoType.dplane}:
                # special case for plane scoring, according to documentation we have:
                #  xmin, ymin, zmin = Sx, Sy, Sz (point on the plane)
                #  xmax, ymax, zmax = nx, ny, nz (normal vector)
                # to avoid situation where i.e. xmax < xmin (corresponds to nx < Sx)
                # we store only point on the plane
                detector.sx, detector.sy, detector.sz = xmin, ymin, zmin
                detector.nx, detector.ny, detector.nz = xmax, ymax, zmax
                xmax = xmin
                ymax = ymin
                zmax = zmin

        xunit, xname = _get_mesh_units(detector, 0)
        yunit, yname = _get_mesh_units(detector, 1)
        zunit, zname = _get_mesh_units(detector, 2)

        detector.x = MeshAxis(n=np.abs(nx), min_val=xmin, max_val=xmax, name=xname, unit=xunit, binning=_bintyp(nx))
        detector.y = MeshAxis(n=np.abs(ny), min_val=ymin, max_val=ymax, name=yname, unit=yunit, binning=_bintyp(ny))
        detector.z = MeshAxis(n=np.abs(nz), min_val=zmin, max_val=zmax, name=zname, unit=zunit, binning=_bintyp(nz))

        detector.dettyp = SHDetType(det_attribs.det_type)

        detector.unit, detector.name = _get_detector_unit(detector.dettyp, detector.geotyp)

    # TODO: we need an alternative list, in case things have been scaled with nscale, since then things
    # are not "/particle" anymore.
    def read_payload(self, detector):
        logger.info("Reading data: " + self.filename)

        if detector.geotyp == SHGeoType.unknown or detector.dettyp == SHDetType.unknown:
            logger.error("Unknown geotyp or dettyp")
            return

        # next read the data:
        offset_str = "S" + str(detector.payload_offset)
        record_dtype = np.dtype([('trash', offset_str),
                                 ('bin2', '<f8', detector.rec_size)])
        record = np.fromfile(self.filename, record_dtype, count=-1)
        # BIN(*)  : a large array holding results. Accessed using pointers.
        detector.data_raw = np.array(record['bin2'][:][0])
        detector.counter = 1

    def read(self, detector):
        self.read_header(detector)
        self.read_payload(detector)


class SHTextReader:
    """
    Reads plain text files with data saved by binary-to-ascii converter.
    """
    def __init__(self, filename):
        self.filename = filename

    def read_header(self, detector):
        raise NotImplementedError

    def read_payload(self, detector):
        raise NotImplementedError

    def read(self, detector):
        self.read_header(detector)
        self.read_payload(detector)
