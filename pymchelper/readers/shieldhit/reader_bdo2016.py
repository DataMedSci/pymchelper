import logging

import numpy as np

from pymchelper.detector import MeshAxis
from pymchelper.readers.shieldhit.reader_base import SHReader, _get_mesh_units, _bintyp, _get_detector_unit, \
    read_next_token
from pymchelper.readers.shieldhit.binary_spec import SHBDOTagID, detector_name_from_bdotag
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from shieldhit.detector.detector_type import SHDetType

logger = logging.getLogger(__name__)


class SHReaderBDO2016(SHReader):
    """
    Binary format reader from version >= 0.6
    """
    def read_data(self, detector):
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
                    detector.mc_code_version = pl[0]
                    logger.debug("MC code version:" + detector.mc_code_version)

                if pl_id == SHBDOTagID.filedate:
                    detector.filedate = pl[0]

                if pl_id == SHBDOTagID.user:
                    detector.user = pl[0]

                if pl_id == SHBDOTagID.host:
                    detector.host = pl[0]

                if pl_id == SHBDOTagID.rt_nstat:
                    detector.number_of_primaries = pl[0]

                # beam configuration etc...
                if pl_id in detector_name_from_bdotag:
                    setattr(detector, detector_name_from_bdotag[pl_id], pl[0])

                # estimator block here ---
                if pl_id == SHBDOTagID.det_geotyp:
                    detector.geotyp = SHGeoType[pl[0].strip().lower()]

                if pl_id == SHBDOTagID.ext_ptvdose:
                    detector.tripdose = 0.0

                if pl_id == SHBDOTagID.ext_nproj:
                    detector.tripntot = -1

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
            logger.debug("Detector nstat: " + str(detector.number_of_primaries))
            logger.debug("Detector nx   : " + str(detector.x.n))
            logger.debug("Detector ny   : " + str(detector.y.n))
            logger.debug("Detector nz   : " + str(detector.z.n))
            detector.file_counter = 1
        super(SHReaderBDO2016, self).read_data(detector)
        return True
