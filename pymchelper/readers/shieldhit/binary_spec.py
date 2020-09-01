from enum import IntEnum


class SHBDOTagID(IntEnum):
    """ List of Tag ID numbers. Must be synchronized with bdotags in sh_detect.h in SH12A.
    """

    # Hex values are used for better recognition in binary files, should they be inspected by humans.
    # Group 0x0000 - 0x00FF : Miscellaneous info
    shversion = 0x00  # [char*] full version string of SHIELD-HIT12A
    shbuilddate = 0x01  # [char*] date of build
    filedate = 0x02  # [char*] bdo file creation date, RFC 2822 compliant
    user = 0x03  # [char *] optional login name
    host = 0x04  # [char *] optional host where this file was created
    format = 0x05  # [int]   optional ID describing which flavour the format is, to help .bdo parsers

    # Group 0xAA00 - 0xAAFF : Runtime variables
    rt_nstat = 0xAA00  # number of actually simulated particles
    rt_time = 0xAA01  # [unsigned long int] optional runtime in seconds

    # Group 0xCB00 - 0xCBFF : Beam configuration
    jpart0 = 0xCB00  # [int] primary particle id
    apro0 = 0xCB01  # [float] number of nucleons a of the beam particles.
    zpro0 = 0xCB02  # [float] charge z of the beam particles.
    beamx = 0xCB03  # [float] start position of the beam - x coordinate
    beamy = 0xCB04  # [float] start position of the beam - y coordinate
    beamz = 0xCB05  # [float] start position of the beam - z coordinate
    sigmax = 0xCB06  # [float] lateral extension of the beam in x direction
    sigmay = 0xCB07  # [float] lateral extension of the beam in y direction
    tmax0 = 0xCB08  # [float] the initial energy of the primary particle
    sigmat0 = 0xCB09  # [float] energy spread of the primary particle
    beamtheta = 0xCB0A  # [float] polar angle
    beamphi = 0xCB0B  # [float] azimuth angle
    beamdivx = 0xCB0C  # [float] beam divergence - x coordinate
    beamdivy = 0xCB0D  # [float] beam divergence - y coordinate
    beamdivk = 0xCB0E  # [float] beam divergence - focus
    tmax0mev = 0xCB0F  # [double] initial projectile energy, always in [MeV]
    tmax0amu = 0xCB10  # [double] initial projectile energy in [MeV/amu] - only written if mass > 0.001 u
    tmax0nuc = 0xCB11  # [double] initial projectile energy in [MeV/nucl] - only written if nucleons > 0

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
    ct_ang = 0xCE00  # holds two doubles with the couch and gantry angle
    ct_icnt = 0xCE01  # holds three
    ct_len = 0xCE02  # holds three

    # Group 0xDD00 - 0xDDFF : Detector/page specific tags
    det_geotyp = 0xDD00  # may differ from est_geotyp in case of spc
    det_nbin = 0xDD01  # idet(1-3) (len=3) number of bins x,y,z
    det_part = 0xDD02  # idet(4) particle type which was scored
    det_dtype = 0xDD03  # idet(5) detector type
    det_partz = 0xDD04  # idet(6)
    det_parta = 0xDD05  # idet(7)
    det_dmat = 0xDD06  # idet(8)
    det_nbine = 0xDD07  # idet(9) number of bins in diff scorer, negative means log binning
    det_difftype = 0xDD08  # idet(10) detector type for differential scorer (i.e. angle, energy, let)
    det_zonestart = 0xDD09  # idet(11)
    det_dsize = 0xDD0A  # idet(12)
    det_dsizexyz = 0xDD0B  # idet(13)

    det_xyz_start = 0xDD0C  # det(1-3)
    det_xyz_stop = 0xDD0D  # det(4-6)
    det_dif_start = 0xDD0E  # det(7)
    det_dif_stop = 0xDD0F  # det(8)
    det_voxvol = 0xDD10  # det(9)
    det_thresh = 0xDD11  # det(10) lower energy scoring threshold

    # Page: meta-data */
    # Group 0xDD30 - 0xDDFF : page specific tags. */
    SHBDO_PAG_TYPE = 0xDD30  # /* detector_type */
    SHBDO_PAG_COUNT = 0xDD31  # /* Number of this detector */
    SHBDO_PAG_NORMALIZE = 0xDD32  # /* == 1 quantity is "per particle", == 0 if not.*/
    SHBDO_PAG_RESCALE = 0xDD33  # /* if set and != 1.0 the data set was multiplied with this factor */
    SHBDO_PAG_OFFSET = 0xDD34  # /* if set and != 0.0 the data set was offset with this value */
    SHBDO_PAG_MEDIUM_TRANSP = 0xDD35  # /* [future] ASCII-string for detector medium set in geo.dat */
    SHBDO_PAG_MEDIUM_SCORE = 0xDD36  # /* [future] ASCII-string for detector medium set in detect.dat scoring */
    SHBDO_PAG_UNITIDS = 0xDD37  # /* Unit IDs according to sh_units.h. Set for detector and the two diff. bins */

    # /* page data */
    det_data = 0xDDBB  # data block
    SHBDO_PAG_DATA = 0xDDBB  # /* data block, identical to SHBDO_DET_DATA */
    SHBDO_PAG_DATA_UNIT = 0xDDBC  # /* ASCII string unit, including any differentials */

    # /* Page differential data */
    SHBDO_PAG_DIF_SET = 0xDDD0  # /* flags if 1 or 2 differential binning was set. 1 for set, -1 for set as log10. */
    SHBDO_PAG_DIF_TYPE = 0xDDD1  # /* array holding 1 or 2 number of bins, for type of differential */
    SHBDO_PAG_DIF_START = 0xDDD2  # /* array holding 1 or 2 lower bounds, for 1-D or 2-D respectively */
    SHBDO_PAG_DIF_STOP = 0xDDD3  # /* array holding 1 or 2 upper bounds, for 1-D or 2-D respectively */
    SHBDO_PAG_DIF_SIZE = 0xDDD4  # /* array holding 1 or 2 number of bins, for 1-D or 2-D respectively */
    SHBDO_PAG_DIF_UNITS = 0xDDD5  # /* ASCII string of ;-separated units along each dimension. */

    # /* Filter data attached to page */
    SHBDO_PAG_FILTER_NAME = 0xDDF0  # /* name of filter containing one or more rules */
    SHBDO_PAG_FILTER_NRULES = 0xDDF1  # /* number of filter rules applied */
    SHBDO_PAG_FILTER_EMIN = 0xDDF2  # /* lower energy threshold, emin */
    SHBDO_PAG_FILTER_EMAX = 0xDDF3  # /* upper energy threshold, emin */

    # Group 0xEE00 - 0xEEFF : Estimator specific tags
    # Geometry, as in gE0metry
    est_geo_type = 0xE000  # geometry type ID, see SH_SGEO_* in sh_scoredef.h
    SHBDO_GEO_NAME = 0xE001  # /* User-given name of this geometry */
    SHBDO_GEO_P = 0xE002  # /* start values, e.g xmin, ymin, zmin */
    SHBDO_GEO_Q = 0xE003  # /* stop values, e.g xmax, ymax, zmax */
    SHBDO_GEO_N = 0xE004  # /* number of bins */
    SHBDO_GEO_ROT = 0xE005  #
    SHBDO_GEO_VOL = 0xE006  #
    SHBDO_GEO_ZONES = 0xE007  #
    SHBDO_GEO_NEQGRID = 0xE008  #
    SHBDO_GEO_UNITS = 0xE009  #
    SHBDO_GEO_UNITIDS = 0xE00A  # /* Unit IDs according to sh_units.h, one unit along each axis. */

    # Group 0xEF00 - 0xEFFF : Estimator
    SHBDO_EST_FILENAME = 0xEE00  # /* number of detectors / pages for this estimator */
    SHBDO_EST_COUNT = 0xEE01  # /* Unique number for this estimator, if several files were saved, starting at 0 */
    SHBDO_EST_NPAGES = 0xEE02  # /* number of detectors / pages for this estimator */
    SHBDO_EST_RESCALE_NSTAT = 0xEE03

    # /* Group 0xFFCC - 0xFFFF : Diagnostics, may be ignored by readers. */
    SHBDO_COMMENT = 0xFFCC  # /* 0xFFCC-omment */
    SHBDO_DEBUG = 0xFFCD  # /* 0xFFCD-ebug */
    SHBDO_ERROR = 0xFFCE  # /* 0xFFCE-rror */


detector_name_from_bdotag = {
    SHBDOTagID.jpart0: 'projectile_code',
    SHBDOTagID.apro0: 'projectile_a',
    SHBDOTagID.zpro0: 'projectile_z',
    SHBDOTagID.beamx: 'projectile_position_x',
    SHBDOTagID.beamy: 'projectile_position_y',
    SHBDOTagID.beamz: 'projectile_position_z',
    SHBDOTagID.sigmax: 'projectile_sigma_x',
    SHBDOTagID.sigmay: 'projectile_sigma_y',
    SHBDOTagID.sigmat0: 'projectile_sigma_energy',
    SHBDOTagID.beamtheta: 'projectile_polar_angle',
    SHBDOTagID.beamphi: 'projectile_azimuth_angle',
    SHBDOTagID.beamdivx: 'projectile_divergence_x',
    SHBDOTagID.beamdivy: 'projectile_divergence_y',
    SHBDOTagID.beamdivk: 'projectile_divergence_k',
    SHBDOTagID.shversion: 'mc_code_version',
    SHBDOTagID.shbuilddate: 'mc_code_build_date',
    SHBDOTagID.filedate: 'filedate',
    SHBDOTagID.user: 'user',
    SHBDOTagID.host: 'host',
    SHBDOTagID.rt_nstat: 'number_of_primaries',
    SHBDOTagID.SHBDO_EST_NPAGES: 'page_count',
    SHBDOTagID.SHBDO_GEO_UNITIDS: 'geo_unit_ids',
    SHBDOTagID.SHBDO_GEO_UNITS: 'geo_units',
    SHBDOTagID.SHBDO_GEO_NAME: 'geo_name',
    SHBDOTagID.tmax0mev: 'Tmax_MeV',
    SHBDOTagID.tmax0amu: 'Tmax_MeV/amu',
    SHBDOTagID.tmax0nuc: 'Tmax_MeV/nucl'
}

page_name_from_bdotag = {
    SHBDOTagID.SHBDO_PAG_RESCALE: 'rescale',
    SHBDOTagID.SHBDO_PAG_OFFSET: 'offset',
    SHBDOTagID.SHBDO_PAG_DIF_TYPE: 'dif_type',
    SHBDOTagID.SHBDO_PAG_DIF_START: 'dif_start',
    SHBDOTagID.SHBDO_PAG_DIF_STOP: 'dif_stop',
    SHBDOTagID.SHBDO_PAG_DIF_SIZE: 'dif_size',
    SHBDOTagID.SHBDO_PAG_DIF_UNITS: 'dif_units',
    SHBDOTagID.SHBDO_PAG_DATA_UNIT: 'data_unit',
    SHBDOTagID.SHBDO_PAG_UNITIDS: 'unit_ids',
}


class SHBDOUnitID(IntEnum):
    SH_SCORING_UNIT_UNKNOWN = -2  # /* e.g. for user defined scoring */
    SH_SCORING_UNIT_INVALID = -1  # /* N/A (not applicable), or undefined */

    SH_SCORING_UNIT_NONE = 0  # /* dimensionless */
    SH_SCORING_UNIT_AU = 1  # /* arbitrary units */
    SH_SCORING_UNIT_PCT = 2  # /* percent (%) */
    SH_SCORING_UNIT_PMIL = 3  # /* promill (%%) */
    SH_SCORING_UNIT_RELATIVE = 4  # /* dimensionless relative fraction */

    SH_SCORING_UNIT_CM = 10  # /* cm */
    SH_SCORING_UNIT_CM2 = 11  # /* cm^2 */
    SH_SCORING_UNIT_CM3 = 12  # /* cm^3 */
    SH_SCORING_UNIT_PCM = 13  # /* cm^-1 */
    SH_SCORING_UNIT_PCM2 = 14  # /* cm^-2 */
    SH_SCORING_UNIT_PCM3 = 15  # /* cm^-3 */

    SH_SCORING_UNIT_M = 16  # /* m */
    SH_SCORING_UNIT_M2 = 17  # /* m^2 */
    SH_SCORING_UNIT_M3 = 18  # /* m^3 */
    SH_SCORING_UNIT_PM = 19  # /* m^-1 */
    SH_SCORING_UNIT_PM2 = 20  # /* m^-2 */
    SH_SCORING_UNIT_PM3 = 21  # /* m^-3 */

    SH_SCORING_UNIT_GPCM3 = 22  # /* density g / cm^3 */
    SH_SCORING_UNIT_KGPM3 = 23  # /* density kg / m^3 */

    SH_SCORING_UNIT_KEVPUM = 30  # /* keV / um */
    SH_SCORING_UNIT_MEVPCM = 31  # /* MeV / cm */
    SH_SCORING_UNIT_MEVCM2PG = 32  # /* MeV * cm^2 / g */

    SH_SCORING_UNIT_MEVPG = 40  # /* MeV / g) */
    SH_SCORING_UNIT_GY = 41  # /* Gy (J/kg) */
    SH_SCORING_UNIT_GYRBE = 42  # /* Gy * RBE */
    SH_SCORING_UNIT_GYRE = 43  # /* Gy * RE (quenching) */
    SH_SCORING_UNIT_SV = 44  # /* Sv (J/kg) */
    SH_SCORING_UNIT_DOSERAD = 45  # /* Rad ( = 1 cGy)  */
    SH_SCORING_UNIT_DOSEREM = 46  # /* Rem ( = 1 cSv)  */

    SH_SCORING_UNIT_DEGREES = 50  # /* degrees */
    SH_SCORING_UNIT_RADIANS = 51  # /* radians */
    SH_SCORING_UNIT_SR = 52  # /* steradian sr = rad^2*/

    SH_SCORING_UNIT_COUNT = 60  # /* number # */

    SH_SCORING_UNIT_MEV = 70  # /* MeV */
    SH_SCORING_UNIT_MEVPNUC = 71  # /* MeV / nucleon */
    SH_SCORING_UNIT_MEVPAMU = 72  # /* MeV / amu */

    SH_SCORING_UNIT_NUCN = 80  # /* number of nucleons */
    SH_SCORING_UNIT_MEVPC2 = 81  # /* particle mass MeV / c^2 */
    SH_SCORING_UNIT_U = 82  # /* particle mass in terms of u */

    SH_SCORING_UNIT_MATID = 90  # /* material ID */
    SH_SCORING_UNIT_NZONE = 91  # /* zone number */


unit_name_from_unit_id = {
    SHBDOUnitID.SH_SCORING_UNIT_NONE: "",
    SHBDOUnitID.SH_SCORING_UNIT_AU: "a.u.",
    SHBDOUnitID.SH_SCORING_UNIT_PCT: "%",
    SHBDOUnitID.SH_SCORING_UNIT_PMIL: "%%",
    SHBDOUnitID.SH_SCORING_UNIT_RELATIVE: "rel.units",

    SHBDOUnitID.SH_SCORING_UNIT_CM: "cm",
    SHBDOUnitID.SH_SCORING_UNIT_CM2: "cm^2",
    SHBDOUnitID.SH_SCORING_UNIT_CM3: "cm^3",
    SHBDOUnitID.SH_SCORING_UNIT_PCM: "/cm",
    SHBDOUnitID.SH_SCORING_UNIT_PCM2: "/cm^2",
    SHBDOUnitID.SH_SCORING_UNIT_PCM3: "/cm^3",

    SHBDOUnitID.SH_SCORING_UNIT_M: "m",
    SHBDOUnitID.SH_SCORING_UNIT_M2: "m^2",
    SHBDOUnitID.SH_SCORING_UNIT_M3: "m^3",
    SHBDOUnitID.SH_SCORING_UNIT_PM: "/m",
    SHBDOUnitID.SH_SCORING_UNIT_PM2: "/m^2",
    SHBDOUnitID.SH_SCORING_UNIT_PM3: "/m^3",

    SHBDOUnitID.SH_SCORING_UNIT_GPCM3: "g/cm^3",
    SHBDOUnitID.SH_SCORING_UNIT_KGPM3: "kg/m^3",

    SHBDOUnitID.SH_SCORING_UNIT_KEVPUM: "keV/um",
    SHBDOUnitID.SH_SCORING_UNIT_MEVPCM: "MeV/cm",
    SHBDOUnitID.SH_SCORING_UNIT_MEVCM2PG: "MeV cm^2/g",

    SHBDOUnitID.SH_SCORING_UNIT_MEVPG: "MeV/g",
    SHBDOUnitID.SH_SCORING_UNIT_GY: "Gy",
    SHBDOUnitID.SH_SCORING_UNIT_GYRBE: "Gy(RBE)",  # /* Probably there are new ICRU rules here */
    SHBDOUnitID.SH_SCORING_UNIT_GYRE: "Gy(RE)",
    SHBDOUnitID.SH_SCORING_UNIT_SV: "Sv",
    SHBDOUnitID.SH_SCORING_UNIT_DOSERAD: "Rad",
    SHBDOUnitID.SH_SCORING_UNIT_DOSEREM: "Rem",

    SHBDOUnitID.SH_SCORING_UNIT_DEGREES: "deg",
    SHBDOUnitID.SH_SCORING_UNIT_RADIANS: "rad",
    SHBDOUnitID.SH_SCORING_UNIT_SR: "sr",

    SHBDOUnitID.SH_SCORING_UNIT_COUNT: "#",

    SHBDOUnitID.SH_SCORING_UNIT_MEV: "MeV",
    SHBDOUnitID.SH_SCORING_UNIT_MEVPNUC: "MeV/nucleon",
    SHBDOUnitID.SH_SCORING_UNIT_MEVPAMU: "MeV/amu",

    SHBDOUnitID.SH_SCORING_UNIT_NUCN: "",
    SHBDOUnitID.SH_SCORING_UNIT_MEVPC2: "MeV/c^2",
    SHBDOUnitID.SH_SCORING_UNIT_U: "u",

    SHBDOUnitID.SH_SCORING_UNIT_MATID: "",
    SHBDOUnitID.SH_SCORING_UNIT_NZONE: "",
}
