import logging

import numpy as np

from pymchelper.detector import Page
from pymchelper.readers.shieldhit.reader_base import SHReader, _get_detector_unit, read_next_token
from pymchelper.readers.shieldhit.binary_spec import SHBDOTagID, detector_name_from_bdotag, page_name_from_bdotag
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

logger = logging.getLogger(__name__)


class SHReaderBDO2019(SHReader):
    """
    Experimental binary format reader version >= 0.7
    """
    def read_data(self, detector):
        logger.debug("Reading: " + self.filename)

        with open(self.filename, "rb") as f:
            d1 = np.dtype([('magic', 'S6'), ('end', 'S2'), ('vstr', 'S16')])

            _x = np.fromfile(f, dtype=d1, count=1)  # read the data into numpy
            logger.debug("Magic : " + _x['magic'][0].decode('ASCII'))
            logger.debug("Endiannes: " + _x['end'][0].decode('ASCII'))
            logger.debug("VerStr: " + _x['vstr'][0].decode('ASCII'))

            while f:
                token = read_next_token(f)
                if token is None:
                    break

                token_id, token_type, payload_len, raw_payload = token

                payload = [None] * payload_len

                # decode all strings (currently there will never be more than one per token)
                if 'S' in token_type.decode('ASCII'):
                    for i, _j in enumerate(raw_payload):
                        payload[i] = raw_payload[i].decode('ASCII').strip()
                else:
                    payload = raw_payload

                if payload_len == 1:
                    payload = payload[0]

                logger.debug("Read token {:s} (0x{:02x}) value {} type {:s} length {:d}".format(
                    SHBDOTagID(token_id).name,
                    token_id,
                    raw_payload,
                    token_type.decode('ASCII'),
                    payload_len
                ))

                # geometry type
                if token_id == SHBDOTagID.est_geo_type:
                    detector.geotyp = SHGeoType[payload.strip().lower()]

                if token_id == SHBDOTagID.SHBDO_GEO_N:
                    detector.x = detector.x._replace(n=payload[0])
                    detector.y = detector.y._replace(n=payload[1])
                    detector.z = detector.z._replace(n=payload[2])

                if token_id == SHBDOTagID.SHBDO_GEO_P:
                    detector.x = detector.x._replace(min_val=payload[0])
                    detector.y = detector.y._replace(min_val=payload[1])
                    detector.z = detector.z._replace(min_val=payload[2])

                if token_id == SHBDOTagID.SHBDO_GEO_Q:
                    detector.x = detector.x._replace(max_val=payload[0])
                    detector.y = detector.y._replace(max_val=payload[1])
                    detector.z = detector.z._replace(max_val=payload[2])

                # detector type
                if token_id == SHBDOTagID.SHBDO_PAG_TYPE:
                    # check if detector type attribute present, if yes, then create new page
                    if detector.pages[-1].dettyp is not None:  # the same tag appears again, looks like new page
                        logger.debug("SHBDO_PAG_TYPE Creating new page no {}".format(len(detector.pages)))
                        detector.pages.append(Page())
                    logger.debug("Setting page.dettyp = {} ({})".format(SHDetType(payload), SHDetType(payload).name))
                    detector.pages[-1].dettyp = SHDetType(payload)

                # detector data
                if token_id == SHBDOTagID.SHBDO_PAG_DATA:
                    # check if data attribute present, if yes, then create new page
                    if detector.pages[-1].data_raw.size > 1:
                        logger.debug("SHBDO_PAG_DATA Creating new page no {}".format(len(detector.pages)))
                        detector.pages.append(Page())
                    elif detector.pages[-1].data_raw.size == 1 and not np.isnan(detector.pages[-1].data_raw[0]):
                        logger.debug("SHBDO_PAG_DATA Creating new page no {}".format(len(detector.pages)))
                        detector.pages.append(Page())
                    logger.debug("Setting page data = {}".format(np.asarray(payload)))
                    detector.pages[-1].data_raw = np.asarray(payload)

                # read tokens based on tag <-> name mapping for detector
                if token_id in detector_name_from_bdotag:
                    logger.debug("Setting detector.{} = {}".format(detector_name_from_bdotag[token_id], payload))
                    setattr(detector, detector_name_from_bdotag[token_id], payload)

                # read tokens based on tag <-> name mapping for pages
                if token_id in page_name_from_bdotag:
                    if hasattr(detector.pages[-1], page_name_from_bdotag[token_id]):
                        logger.debug("page_name_from_bdotag Creating new page no {}".format(len(detector.pages)))
                        detector.pages.append(Page())
                    logger.debug("Setting page.{} = {}".format(page_name_from_bdotag[token_id], payload))
                    setattr(detector.pages[-1], page_name_from_bdotag[token_id], payload)

                # # TODO implement double differential scoring
                # if token_id == SHBDOTagID.SHBDO_PAG_DIF_SIZE:
                #     detector.dif_n = payload
                #
                # if token_id == SHBDOTagID.SHBDO_PAG_DIF_START:
                #     detector.dif_min = payload
                #
                # if token_id == SHBDOTagID.SHBDO_PAG_DIF_STOP:
                #     detector.dif_max = payload
                #
                # if token_id == SHBDOTagID.SHBDO_PAG_DIF_TYPE:
                #     detector.dif_type = payload

                # if token_id == SHBDOTagID.SHBDO_PAG_DATA:
                #     logger.debug("page count {}".format(detector.page_count))
                #
                #     # data_raw is defined as None just before the loop
                #     if hasattr(detector, 'page_count') and detector.page_count > 1:
                #         if data_raw:
                #             data_raw.append(np.asarray(payload))  # data from subsequent page
                #         else:
                #             data_raw = [np.asarray(payload)]  # data from first page
                #     else:  # information about pages is not parsed yet
                #         data_raw = np.asarray(payload)

            # # differential scoring data replacement
            # if hasattr(detector, 'dif_min') and hasattr(detector, 'dif_max') and hasattr(detector, 'dif_n'):
            #     if nz == 1:
            #         # max two axis (X or Y) filled with scored value, Z axis empty
            #         # we can put differential quantity as Z axis
            #         nz = detector.dif_n
            #         zmin = detector.dif_min
            #         zmax = detector.dif_max
            #         detector.dif_axis = 2
            #     elif ny == 1:
            #         # Z axis filled with scored value (X axis maybe also), Y axis empty
            #         # we can put differential quantity as Y axis
            #         ny = detector.dif_n
            #         ymin = detector.dif_min
            #         ymax = detector.dif_max
            #         detector.dif_axis = 1
            #     elif nx == 1:
            #         nx = detector.dif_n
            #         xmin = detector.dif_min
            #         xmax = detector.dif_max
            #         detector.dif_axis = 0

            # xunit, xname = _get_mesh_units(detector, 0)
            # yunit, yname = _get_mesh_units(detector, 1)
            # zunit, zname = _get_mesh_units(detector, 2)

            detector.unit, detector.name = _get_detector_unit(detector.dettyp[0], detector.geotyp)

            logger.debug("Done reading bdo file.")
            return True
