import logging

import numpy as np

from pymchelper.estimator import Page, MeshAxis
from pymchelper.readers.shieldhit.reader_base import SHReader, read_next_token
from pymchelper.readers.shieldhit.binary_spec import SHBDOTagID, detector_name_from_bdotag, page_name_from_bdotag, \
    unit_name_from_unit_id
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

logger = logging.getLogger(__name__)


class SHReaderBDO2019(SHReader):
    """
    Experimental binary format reader version >= 0.7
    """
    def read_data(self, estimator):
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
                    estimator.geotyp = SHGeoType[payload.strip().lower()]

                if token_id == SHBDOTagID.SHBDO_GEO_N:
                    estimator.x = estimator.x._replace(n=payload[0])
                    estimator.y = estimator.y._replace(n=payload[1])
                    estimator.z = estimator.z._replace(n=payload[2])

                if token_id == SHBDOTagID.SHBDO_GEO_P:
                    estimator.x = estimator.x._replace(min_val=payload[0])
                    estimator.y = estimator.y._replace(min_val=payload[1])
                    estimator.z = estimator.z._replace(min_val=payload[2])

                if token_id == SHBDOTagID.SHBDO_GEO_Q:
                    estimator.x = estimator.x._replace(max_val=payload[0])
                    estimator.y = estimator.y._replace(max_val=payload[1])
                    estimator.z = estimator.z._replace(max_val=payload[2])

                if token_id == SHBDOTagID.SHBDO_GEO_UNITIDS:
                    estimator.x = estimator.x._replace(unit=unit_name_from_unit_id.get(payload[0], ""))
                    estimator.y = estimator.y._replace(unit=unit_name_from_unit_id.get(payload[1], ""))
                    estimator.z = estimator.z._replace(unit=unit_name_from_unit_id.get(payload[2], ""))

                # detector type
                if token_id == SHBDOTagID.SHBDO_PAG_TYPE:
                    # check if detector type attribute present, if yes, then create new page
                    if estimator.pages[-1].dettyp is not None:  # the same tag appears again, looks like new page
                        logger.debug("SHBDO_PAG_TYPE Creating new page no {}".format(len(estimator.pages)))
                        estimator.add_page(Page())
                    logger.debug("Setting page.dettyp = {} ({})".format(SHDetType(payload), SHDetType(payload).name))
                    estimator.pages[-1].dettyp = SHDetType(payload)

                # detector data
                if token_id == SHBDOTagID.SHBDO_PAG_DATA:
                    # check if data attribute present, if yes, then create new page
                    if estimator.pages[-1].data_raw.size > 1:
                        logger.debug("SHBDO_PAG_DATA Creating new page no {}".format(len(estimator.pages)))
                        estimator.add_page(Page())
                    elif estimator.pages[-1].data_raw.size == 1 and not np.isnan(estimator.pages[-1].data_raw[0]):
                        logger.debug("SHBDO_PAG_DATA Creating new page no {}".format(len(estimator.pages)))
                        estimator.add_page(Page())
                    logger.debug("Setting page data = {}".format(np.asarray(payload)))
                    estimator.pages[-1].data_raw = np.asarray(payload)

                # read tokens based on tag <-> name mapping for detector
                if token_id in detector_name_from_bdotag:
                    logger.debug("Setting detector.{} = {}".format(detector_name_from_bdotag[token_id], payload))
                    setattr(estimator, detector_name_from_bdotag[token_id], payload)

                # read tokens based on tag <-> name mapping for pages
                if token_id in page_name_from_bdotag:
                    if hasattr(estimator.pages[-1], page_name_from_bdotag[token_id]):
                        logger.debug("page_name_from_bdotag Creating new page no {}".format(len(estimator.pages)))
                        estimator.add_page(Page())
                    logger.debug("Setting page.{} = {}".format(page_name_from_bdotag[token_id], payload))
                    setattr(estimator.pages[-1], page_name_from_bdotag[token_id], payload)

            for page in estimator.pages:
                diff_level_1_size = getattr(page, 'dif_size', [0, 0])[0]
                if diff_level_1_size > 1 and hasattr(page, 'dif_start') and hasattr(page, 'dif_stop'):
                    page.diff_axis1 = MeshAxis(n=diff_level_1_size,
                                               min_val=page.dif_start[0],
                                               max_val=page.dif_stop[0],
                                               name="",
                                               unit="",
                                               binning=MeshAxis.BinningType.linear)

            logger.debug("Done reading bdo file.")
            return True
