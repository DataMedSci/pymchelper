import logging

import numpy as np

from pymchelper.axis import MeshAxis
from pymchelper.page import Page
from pymchelper.readers.shieldhit.reader_base import SHReader, mesh_unit_and_name, _bintyp, _get_detector_unit, \
    read_next_token, safe_dettyp
from pymchelper.readers.shieldhit.binary_spec import SHBDOTagID, detector_name_from_bdotag
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

logger = logging.getLogger(__name__)


class SHReaderBDO2016(SHReader):
    """
    Binary format reader from version >= 0.6
    This format doesn't have support for multiple pages per estimator
    """

    @staticmethod
    def _decode_payload(payload_type, raw_payload, payload_len):
        payload = [None] * payload_len

        if 'S' in payload_type.decode('ASCII'):
            for i, _ in enumerate(raw_payload):
                payload[i] = raw_payload[i].decode('ASCII').strip()
        else:
            payload = raw_payload

        return payload

    @staticmethod
    def _log_token(token_id, payload_type, payload_len, raw_payload):
        try:
            token_name = SHBDOTagID(token_id).name
            logger.debug("Read token {:s} (0x{:02x}) value {} type {:s} length {:d}".format(
                token_name,
                token_id,
                raw_payload,
                payload_type.decode('ASCII'),
                payload_len
            ))
        except ValueError:
            logger.info("Skipping token (0x{:02x}) value {} type {:s} length {:d}".format(
                token_id,
                raw_payload,
                payload_type.decode('ASCII'),
                payload_len
            ))

    @staticmethod
    def _update_differential_scoring(estimator, token_id, payload):
        diff_geotypes = {SHGeoType.dplane, SHGeoType.dmsh, SHGeoType.dcyl, SHGeoType.dzone}
        if not hasattr(estimator, 'geotyp') or estimator.geotyp not in diff_geotypes:
            return

        if SHBDOTagID.det_dif_start == token_id:
            estimator.dif_min = payload[0]

        if SHBDOTagID.det_dif_stop == token_id:
            estimator.dif_max = payload[0]

        if SHBDOTagID.det_nbine == token_id:
            estimator.dif_n = payload[0]

        if SHBDOTagID.det_difftype == token_id:
            estimator.dif_type = payload[0]

    @staticmethod
    def _update_run_metadata(estimator, token_id, payload):
        if SHBDOTagID.shversion == token_id:
            estimator.mc_code_version = payload[0]
            logger.debug("MC code version:" + estimator.mc_code_version)

        if SHBDOTagID.filedate == token_id:
            estimator.filedate = payload[0]

        if SHBDOTagID.user == token_id:
            estimator.user = payload[0]

        if SHBDOTagID.host == token_id:
            estimator.host = payload[0]

        if SHBDOTagID.rt_nstat == token_id:
            estimator.number_of_primaries = payload[0]

        if token_id in detector_name_from_bdotag:
            setattr(estimator, detector_name_from_bdotag[token_id], payload[0])

        if SHBDOTagID.det_geotyp == token_id:
            estimator.geotyp = SHGeoType[payload[0].strip().lower()]

        if SHBDOTagID.ext_ptvdose == token_id:
            estimator.tripdose = 0.0

        if SHBDOTagID.ext_nproj == token_id:
            estimator.tripntot = -1

    @staticmethod
    def _update_page_metadata(estimator, token_id, payload):
        if SHBDOTagID.det_dtype == token_id:
            estimator.pages[0].dettyp = safe_dettyp(payload[0])

        if SHBDOTagID.det_part == token_id:
            estimator.scored_particle_code = payload[0]
        if SHBDOTagID.det_partz == token_id:
            estimator.scored_particle_z = payload[0]
        if SHBDOTagID.det_parta == token_id:
            estimator.scored_particle_a = payload[0]

        if SHBDOTagID.data_block == token_id:
            estimator.pages[0].data_raw = np.asarray(payload)

    @staticmethod
    def _update_geometry_data(estimator, token_id, payload, geometry_data):
        if SHBDOTagID.det_nbin == token_id:
            geometry_data['nx'] = payload[0]
            geometry_data['ny'] = payload[1]
            geometry_data['nz'] = payload[2]

        if SHBDOTagID.det_xyz_start == token_id:
            geometry_data['xmin'] = payload[0]
            geometry_data['ymin'] = payload[1]
            geometry_data['zmin'] = payload[2]

        if SHBDOTagID.det_xyz_stop == token_id:
            geometry_data['xmax'] = payload[0]
            geometry_data['ymax'] = payload[1]
            geometry_data['zmax'] = payload[2]

        if SHBDOTagID.det_zonestart == token_id:
            estimator.zone_start = payload[0]

    @staticmethod
    def _update_estimator(estimator, token_id, payload, geometry_data):
        SHReaderBDO2016._update_run_metadata(estimator, token_id, payload)
        SHReaderBDO2016._update_page_metadata(estimator, token_id, payload)
        SHReaderBDO2016._update_geometry_data(estimator, token_id, payload, geometry_data)
        SHReaderBDO2016._update_differential_scoring(estimator, token_id, payload)

    @staticmethod
    def _prepare_geometry(estimator, geometry_data):
        nx = geometry_data['nx']
        ny = geometry_data['ny']
        nz = geometry_data['nz']
        xmin = geometry_data['xmin']
        ymin = geometry_data['ymin']
        zmin = geometry_data['zmin']
        xmax = geometry_data['xmax']
        ymax = geometry_data['ymax']
        zmax = geometry_data['zmax']

        if estimator.geotyp in {SHGeoType.zone, SHGeoType.dzone}:
            xmin = estimator.zone_start
            xmax = xmin + nx - 1
            ymin = 0.0
            ymax = 0.0
            zmin = 0.0
            zmax = 0.0
        elif estimator.geotyp in {SHGeoType.plane, SHGeoType.dplane}:
            estimator.sx, estimator.sy, estimator.sz = xmin, ymin, zmin
            estimator.nx, estimator.ny, estimator.nz = xmax, ymax, zmax
            xmax = xmin
            ymax = ymin
            zmax = zmin

        if hasattr(estimator, 'dif_type') and estimator.dif_type == 2:
            estimator.dif_min /= 10.0
            estimator.dif_max /= 10.0

        if hasattr(estimator, 'dif_min') and hasattr(estimator, 'dif_max') and hasattr(estimator, 'dif_n'):
            if nz == 1:
                nz = estimator.dif_n
                zmin = estimator.dif_min
                zmax = estimator.dif_max
                estimator.dif_axis = 2
            elif ny == 1:
                ny = estimator.dif_n
                ymin = estimator.dif_min
                ymax = estimator.dif_max
                estimator.dif_axis = 1
            elif nx == 1:
                nx = estimator.dif_n
                xmin = estimator.dif_min
                xmax = estimator.dif_max
                estimator.dif_axis = 0

        return nx, ny, nz, xmin, ymin, zmin, xmax, ymax, zmax

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

            # if no pages are present, add first one
            if not estimator.pages:
                estimator.add_page(Page())

            geometry_data = {
                'nx': None,
                'ny': None,
                'nz': None,
                'xmin': None,
                'ymin': None,
                'zmin': None,
                'xmax': None,
                'ymax': None,
                'zmax': None,
            }

            while f:
                token = read_next_token(f)
                if token is None:
                    break

                pl_id, _pl_type, _pl_len, _pl = token
                pl = self._decode_payload(_pl_type, _pl, _pl_len)
                self._log_token(pl_id, _pl_type, _pl_len, _pl)
                self._update_estimator(estimator, pl_id, pl, geometry_data)

            if None in {geometry_data['nx'], geometry_data['ny'], geometry_data['nz']}:
                logger.error("Missing det_nbin tag in BDO2016 file")
                return False

            nx, ny, nz, xmin, ymin, zmin, xmax, ymax, zmax = self._prepare_geometry(estimator, geometry_data)

            xunit, xname = mesh_unit_and_name(estimator, 0)
            yunit, yname = mesh_unit_and_name(estimator, 1)
            zunit, zname = mesh_unit_and_name(estimator, 2)

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

            estimator.file_format = 'bdo2016'
            estimator.data_order = 'F'  # Fortran column-major order

            logger.debug("Done reading bdo file.")
            logger.debug("Detector data : " + str(estimator.pages[0].data))
            logger.debug("Detector nstat: " + str(estimator.number_of_primaries))
            logger.debug("Detector nx   : " + str(estimator.x.n))
            logger.debug("Detector ny   : " + str(estimator.y.n))
            logger.debug("Detector nz   : " + str(estimator.z.n))
            estimator.file_counter = 1
        super(SHReaderBDO2016, self).read_data(estimator)
        return True
