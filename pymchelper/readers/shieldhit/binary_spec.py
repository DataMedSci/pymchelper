from enum import IntEnum


class SHBDOTagID(IntEnum):
    """ List of Tag ID numbers for BDO 2016 and 2019 formats.
    Must be synchronized with tags in sh_bdo.h and sh_detect.h in SH12A.
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
    rt_timesim = 0xAA02  # optional simulation time in seconds, excluding initialization.

    # Group 0xCB00 - 0xCBFF : Beam configuration
    jpart0 = 0xCB00  # [int] primary particle ID, in SH12A JPART terminology (32768 = INVALID)
    apro0 = 0xCB01  # [int] number of nucleons A of the projectile - only written if nucleons > 0
    zpro0 = 0xCB02  # [int] charge Z of the projectile, may also be negative (32768 = INVALID)
    beamx = 0xCB03  # [float] start position of the beam - X coordinate
    beamy = 0xCB04  # [float] start position of the beam - Y coordinate
    beamz = 0xCB05  # [float] start position of the beam - Z coordinate
    sigmax = 0xCB06  # [float] lateral extension of the beam in X direction
    sigmay = 0xCB07  # [float] lateral extension of the beam in Y direction
    tmax0 = 0xCB08  # [float] initial projectile energy (unit depends on projectile type)
    sigmat0 = 0xCB09  # [float] energy spread of the primary particle
    beamtheta = 0xCB0A  # [float] polar angle
    beamphi = 0xCB0B  # [float] azimuth angle
    beamdivx = 0xCB0C  # [float] beam divergence - X coordinate
    beamdivy = 0xCB0D  # [float] beam divergence - Y coordinate
    beamdivk = 0xCB0E  # [float] beam divergence - focus
    tmax0mev = 0xCB0F  # [double] initial projectile energy, always in [MeV]
    tmax0amu = 0xCB10  # [double] initial projectile energy in [MeV/amu] - only written if mass > 1e-6 u
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

    # Group 0xDD00 - 0xDD11 : old detect.f fortran Detector / page specific tags. See sh_detect.h
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
    detector_type = 0xDD30  # /* detector_type, this starts new page */
    page_number = 0xDD31  # /* Number of this detector */
    page_normalized = 0xDD32  # Flags for page->postproc on how to postprocess the data in SHBDO_PAG_DATA
    """
    Given:
        - the data in page->data as x_j
        - for j instances of this simulation
        - which was done with I_j number of paritcles.

        The resulting data will be termed X and has the units given by SHBDO_PAG_DATA_UNIT

        0: X = x_1                                for GEOMAP type scorers
        1: X = sum_j x_j                          COUNT, ...
        2: X = (sum_j x_j) / (sum_j I_j)          NORMCOUNT, ...
        3: X = (sum_j x_j * I_j) / (sum_j I_j)    LET, ...
    """

    page_scale_factor = 0xDD33  # /* if set and != 1.0 the data set was multiplied with this factor */
    page_offset = 0xDD34  # /* if set and != 0.0 the data set was offset with this value */
    page_medium_transport = 0xDD35  # /* [future] ASCII-string for detector medium set in geo.dat */
    page_medium_scoring = 0xDD36  # /* [future] ASCII-string for detector medium set in detect.dat scoring */
    page_unit_ids = 0xDD37  # /* Unit IDs according to sh_units.h. Set for detector and the two diff. bins */

    # /* page data */
    data_block = 0xDDBB  # /* data block, identical to SHBDO_DET_DATA */
    detector_unit = 0xDDBC  # /* ASCII string unit, including any differentials */

    # /* Page differential data */
    page_diff_flag = 0xDDD0  # /* flags if 1 or 2 differential binning was set. 1 for set, -1 for set as log10. */
    page_diff_type = 0xDDD1  # /* array holding 1 or 2 number of bins, for type of differential */
    page_diff_start = 0xDDD2  # /* array holding 1 or 2 lower bounds, for 1-D or 2-D respectively */
    page_diff_stop = 0xDDD3  # /* array holding 1 or 2 upper bounds, for 1-D or 2-D respectively */
    page_diff_size = 0xDDD4  # /* array holding 1 or 2 number of bins, for 1-D or 2-D respectively */
    page_diff_units = 0xDDD5  # /* ASCII string of ;-separated units along each dimension. %s;%s;%s where latter
    #          two %s are the differential units, and the first is the data in
    #          non-differential form. */

    # /* Filter data attached to page */
    page_filter_name = 0xDDF0  # /* name of filter containing one or more rules */
    page_filter_rules_no = 0xDDF1  # /* number of filter rules applied */
    page_filter_e_min = 0xDDF2  # /* lower energy threshold, emin */
    page_filter_emax = 0xDDF3  # /* upper energy threshold, emin */

    # Group 0xEE00 - 0xEEFF : Estimator specific tags
    # Geometry, as in gE0metry
    geometry_type = 0xE000  # geometry type ID, see SH_SGEO_* in sh_scoredef.h
    geometry_name = 0xE001  # /* User-given name of this geometry */
    geo_p_start = 0xE002  # /* start values, e.g xmin, ymin, zmin */
    geo_q_stop = 0xE003  # /* stop values, e.g xmax, ymax, zmax */
    geo_n_bins = 0xE004  # /* number of bins */
    geo_rotation = 0xE005  # [future] rotation of geometry
    geo_volume = 0xE006  # volume size in cm3 ... WARNING: may be a list in some future
    geo_zones = 0xE007  # single GEMCA zone, or list of zones
    geo_non_equidist_grid = 0xE008  # Array of non-equidistant z-grid. Tag only used if set.
    geo_units = 0xE009  # [Future]: ASCII string of ;-separated units along each dimension.
    geo_unit_ids = 0xE00A  # /* Unit IDs according to sh_units.h, one unit along each axis. */

    # Group 0xEF00 - 0xEFFF : Estimator
    filename_or_geotype = 0xEE00  # /* filename (bdo2019 format) or geometry name (bdo2016 format)*/
    estimator_number = 0xEE01  # /* Unique number for this estimator, if several files were saved, starting at 0 */
    number_of_pages = 0xEE02  # /* number of detectors / pages for this estimator */
    estimator_rescale_per_particle = 0xEE03  # estimator "per particle" rescaling, absent or set to 1 if no rescaling
    # note, that written data will *not* be multiplied with this value, it is up
    # to the BDO reader to multiply with this, if SHBDO_PAGE_NORMALIZE was set

    # /* Group 0xFFCC - 0xFFFF : Diagnostics, may be ignored by readers. */
    comment = 0xFFCC  # /* 0xFFCC-omment */
    debug = 0xFFCD  # /* 0xFFCD-ebug */
    error = 0xFFCE  # /* 0xFFCE-rror */


estimator_tags_to_save = (

)

page_tags_to_save = (
    SHBDOTagID.detector_type,
    SHBDOTagID.page_number,
    SHBDOTagID.page_normalized,
    SHBDOTagID.page_scale_factor,
    SHBDOTagID.page_offset,
    SHBDOTagID.page_unit_ids,

    SHBDOTagID.detector_unit,

    SHBDOTagID.page_diff_flag,
    SHBDOTagID.page_diff_type,
    SHBDOTagID.page_diff_start,
    SHBDOTagID.page_diff_stop,
    SHBDOTagID.page_diff_size,
    SHBDOTagID.page_diff_units,

    SHBDOTagID.page_filter_name,
    SHBDOTagID.page_filter_rules_no,
    SHBDOTagID.page_filter_e_min,
    SHBDOTagID.page_filter_emax,
)

# replace this dictionary with tuple estimator_tags_to_save
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
    SHBDOTagID.number_of_pages: 'page_count',
    SHBDOTagID.geo_unit_ids: 'geo_unit_ids',
    SHBDOTagID.geo_units: 'geo_units',
    SHBDOTagID.geometry_name: 'geo_name',
    SHBDOTagID.tmax0mev: 'Tmax_MeV',
    SHBDOTagID.tmax0amu: 'Tmax_MeV/amu',
    SHBDOTagID.tmax0nuc: 'Tmax_MeV/nucl'
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
