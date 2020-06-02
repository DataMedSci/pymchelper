import logging

import numpy as np

from pymchelper.estimator import MeshAxis
from pymchelper.readers.shieldhit.reader_base import SHReader, _get_mesh_units, _bintyp, _get_detector_unit, \
    read_next_token
from pymchelper.readers.shieldhit.binary_spec import SHBDOTagID, detector_name_from_bdotag
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.shieldhit.detector.detector_type import SHDetType

logger = logging.getLogger(__name__)


class SHReaderBDO2016(SHReader):
    """
    Binary format reader from version >= 0.6
    """
    def read_data(self, estimator):
        logger.debug("Reading: " + self.filename)
        with open(self.filename, "rb") as f:
            d1 = np.dtype([('magic', 'S6'),
                           ('end', 'S2'),
                           ('vstr', 'S16')])

            _x = np.fromfile(f, dtype=d1, count=1)  # read the data into numpy
            logger.debug("Magic : " + _x['magic'][0].decode('ASCII'))
            logger.debug("Endian: " + _x['end'][0].decode('ASCII'))
            logger.debug("VerStr: " + _x['vstr'][0].decode('ASCII'))

            while f:
                token = read_next_token(f)
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

                logger.debug("Read token {:s} (0x{:02x}) value {} type {:s} length {:d}".format(
                    SHBDOTagID(pl_id).name,
                    pl_id,
                    _pl,
                    _pl_type.decode('ASCII'),
                    _pl_len
                ))

                if pl_id == SHBDOTagID.shversion:
                    estimator.mc_code_version = pl[0]
                    logger.debug("MC code version:" + estimator.mc_code_version)

                if pl_id == SHBDOTagID.filedate:
                    estimator.filedate = pl[0]

                if pl_id == SHBDOTagID.user:
                    estimator.user = pl[0]

                if pl_id == SHBDOTagID.host:
                    estimator.host = pl[0]

                if pl_id == SHBDOTagID.rt_nstat:
                    estimator.number_of_primaries = pl[0]

                # beam configuration etc...
                if pl_id in detector_name_from_bdotag:
                    setattr(estimator, detector_name_from_bdotag[pl_id], pl[0])

                # estimator block here ---
                if pl_id == SHBDOTagID.det_geotyp:
                    estimator.geotyp = SHGeoType[pl[0].strip().lower()]

                if pl_id == SHBDOTagID.ext_ptvdose:
                    estimator.tripdose = 0.0

                if pl_id == SHBDOTagID.ext_nproj:
                    estimator.tripntot = -1

                # read a single detector
                if pl_id == SHBDOTagID.det_dtype:
                    estimator.pages[0].dettyp = SHDetType(pl[0])

                if pl_id == SHBDOTagID.det_part:  # particle to be scored
                    estimator.scored_particle_code = pl[0]
                if pl_id == SHBDOTagID.det_partz:  # particle to be scored
                    estimator.scored_particle_z = pl[0]
                if pl_id == SHBDOTagID.det_parta:  # particle to be scored
                    estimator.scored_particle_a = pl[0]

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
                if hasattr(estimator, 'geotyp') and estimator.geotyp in diff_geotypes:
                    if pl_id == SHBDOTagID.det_dif_start:
                        estimator.dif_min = pl[0]

                    if pl_id == SHBDOTagID.det_dif_stop:
                        estimator.dif_max = pl[0]

                    if pl_id == SHBDOTagID.det_nbine:
                        estimator.dif_n = pl[0]

                    if pl_id == SHBDOTagID.det_difftype:
                        estimator.dif_type = pl[0]

                if pl_id == SHBDOTagID.det_zonestart:
                    estimator.zone_start = pl[0]

                if pl_id == SHBDOTagID.det_data:
                    estimator.pages[0].data_raw = np.asarray(pl)

            # TODO: would be better to not overwrite x,y,z and make proper case for ZONE scoring later.
            if estimator.geotyp in {SHGeoType.zone, SHGeoType.dzone}:
                # special case for zone scoring, x min and max will be zone numbers
                xmin = estimator.zone_start
                xmax = xmin + nx - 1
                ymin = 0.0
                ymax = 0.0
                zmin = 0.0
                zmax = 0.0
            elif estimator.geotyp in {SHGeoType.plane, SHGeoType.dplane}:
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

            # check if scoring quantity is LET, if yes, than change units from [MeV/cm] to [keV/um]
            if hasattr(estimator, 'dif_type') and estimator.dif_type == 2:
                estimator.dif_min /= 10.0
                estimator.dif_max /= 10.0

            # # differential scoring data replacement
            if hasattr(estimator, 'dif_min') and hasattr(estimator, 'dif_max') and hasattr(estimator, 'dif_n'):
                if nz == 1:
                    # max two axis (X or Y) filled with scored value, Z axis empty
                    # we can put differential quantity as Z axis
                    nz = estimator.dif_n
                    zmin = estimator.dif_min
                    zmax = estimator.dif_max
                    estimator.dif_axis = 2
                elif ny == 1:
                    # Z axis filled with scored value (X axis maybe also), Y axis empty
                    # we can put differential quantity as Y axis
                    ny = estimator.dif_n
                    ymin = estimator.dif_min
                    ymax = estimator.dif_max
                    estimator.dif_axis = 1
                elif nx == 1:
                    nx = estimator.dif_n
                    xmin = estimator.dif_min
                    xmax = estimator.dif_max
                    estimator.dif_axis = 0

            xunit, xname = _get_mesh_units(estimator, 0)
            yunit, yname = _get_mesh_units(estimator, 1)
            zunit, zname = _get_mesh_units(estimator, 2)

            estimator.x = MeshAxis(n=np.abs(nx),
                                   min_val=xmin,
                                   max_val=xmax,
                                   name=xname,
                                   unit=xunit,
                                   binning=_bintyp(nx))
            estimator.y = MeshAxis(n=np.abs(ny),
                                   min_val=ymin,
                                   max_val=ymax,
                                   name=yname,
                                   unit=yunit,
                                   binning=_bintyp(ny))
            estimator.z = MeshAxis(n=np.abs(nz),
                                   min_val=zmin,
                                   max_val=zmax,
                                   name=zname,
                                   unit=zunit,
                                   binning=_bintyp(nz))

            estimator.pages[0].unit, estimator.pages[0].name = _get_detector_unit(estimator.pages[0].dettyp,
                                                                                  estimator.geotyp)

            logger.debug("Done reading bdo file.")
            logger.debug("Detector data : " + str(estimator.data))
            logger.debug("Detector nstat: " + str(estimator.number_of_primaries))
            logger.debug("Detector nx   : " + str(estimator.x.n))
            logger.debug("Detector ny   : " + str(estimator.y.n))
            logger.debug("Detector nz   : " + str(estimator.z.n))
            estimator.file_counter = 1
        super(SHReaderBDO2016, self).read_data(estimator)
        return True
