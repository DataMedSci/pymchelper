from enum import IntEnum


class SHBDOTagID(IntEnum):
    """ List of Tag ID numbers. Must be synchronized with sh_detect.h in SH12A.
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

    det_data = 0xDDBB  # data block

    # Group 0xEE00 - 0xEEFF : Estimator specific tags
    # Geometry, as in gE0metry
    est_geo_type = 0xE000  # geometry type ID, see SH_SGEO_* in sh_scoredef.h
    SHBDO_GEO_NAME = 0xE001  # number of detectors / pages for this estimator
    SHBDO_GEO_P = 0xE002  #
    SHBDO_GEO_Q = 0xE003  #
    SHBDO_GEO_N = 0xE004  #
    SHBDO_GEO_ROT = 0xE005  #
    SHBDO_GEO_VOL = 0xE006  #
    SHBDO_GEO_ZONES = 0xE007  #
    SHBDO_GEO_NEQGRID = 0xE008  #
    SHBDO_GEO_UNITS = 0xE009  #

    # Group 0xEF00 - 0xEFFF : Estimator
    SHBDO_EST_FILENAME = 0xEE00  # /* number of detectors / pages for this estimator */
    SHBDO_EST_COUNT = 0xEE01  # /* Unique number for this estimator, if several files were saved, starting at 0 */
    SHBDO_EST_NPAGES = 0xEE02  # /* number of detectors / pages for this estimator */
    SHBDO_EST_RESCALE_NSTAT = 0xEE03

    # Page: meta-data */
    # Group 0xDD30 - 0xDDFF : page specific tags. */
    SHBDO_PAG_TYPE = 0xDD30  # /* detector_type */
    SHBDO_PAG_COUNT = 0xDD31  # /* Number of this detector */
    SHBDO_PAG_NORMALIZE = 0xDD32  # /* == 1 quantity is "per particle", == 0 if not.*/
    SHBDO_PAG_RESCALE = 0xDD33  # /* if set and != 1.0 the data set was multiplied with this factor */
    SHBDO_PAG_OFFSET = 0xDD34  # /* if set and != 0.0 the data set was offset with this value */
    SHBDO_PAG_MEDIUM_TRANSP = 0xDD35  # /* [future] ASCII-string for detector medium set in geo.dat */
    SHBDO_PAG_MEDIUM_SCORE = 0xDD36  # /* [future] ASCII-string for detector medium set in detect.dat scoring */

    # /* page data */
    SHBDO_PAG_DATA = 0xDDBB  # /* data block, identical to SHBDO_DET_DATA */
    SHBDO_PAG_DATA_UNIT = 0xDDBC  # /* [future] ASCII string unit */

    # /* Page differential data */
    SHBDO_PAG_DIF_SET = 0xDDD0  # /* flags if 1 or 2 differential binning was set. 1 for set, -1 for set as log10. */
    SHBDO_PAG_DIF_TYPE = 0xDDD1  # /* array holding 1 or 2 number of bins, for type of differential */
    SHBDO_PAG_DIF_START = 0xDDD2  # /* array holding 1 or 2 lower bounds, for 1-D or 2-D respectively */
    SHBDO_PAG_DIF_STOP = 0xDDD3  # /* array holding 1 or 2 upper bounds, for 1-D or 2-D respectively */
    SHBDO_PAG_DIF_SIZE = 0xDDD4  # /* array holding 1 or 2 number of bins, for 1-D or 2-D respectively */
    SHBDO_PAG_DIF_UNITS = 0xDDD5  # /* [Future]: ASCII string of ;-separated units along each dimension. */

    # /* Filter data attached to page */
    SHBDO_PAG_FILTER_NAME = 0xDDF0  # /* name of filter containing one or more rules */
    SHBDO_PAG_FILTER_NRULES = 0xDDF1  # /* number of filter rules applied */
    SHBDO_PAG_FILTER_EMIN = 0xDDF2  # /* lower energy threshold, emin */
    SHBDO_PAG_FILTER_EMAX = 0xDDF3  # /* upper energy threshold, emin */

    # /* Group 0xAA00 - 0xAAFF : Runtime variables */
    SHBDO_RT_NSTAT = 0xAA00  # /* number of actually simulated particles */
    SHBDO_RT_TIME = 0xAA01  # /* [usignend long int] optional runtime in seconds */

    # /* Group 0xFFCC - 0xFFFF : Diagnostics, may be ignored by readers. */
    SHBDO_COMMENT = 0xFFCC  # /* 0xFFCC-omment */
    SHBDO_DEBUG = 0xFFCD  # /* 0xFFCD-ebug */
    SHBDO_ERROR = 0xFFCE  # /* 0xFFCE-rror */


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
