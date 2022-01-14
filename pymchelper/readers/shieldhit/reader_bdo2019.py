import logging

import numpy as np

from pymchelper.axis import MeshAxis
from pymchelper.page import Page
from pymchelper.readers.shieldhit.binary_spec import SHBDOTagID, detector_name_from_bdotag, unit_name_from_unit_id, \
    page_tags_to_save
from pymchelper.readers.shieldhit.reader_base import SHReader, read_next_token, mesh_unit_and_name
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

logger = logging.getLogger(__name__)


class SHReaderBDO2019(SHReader):
    """Experimental binary format reader version >= 0.7"""

    def read_data(self, estimator, nscale=1):
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
                _has_geo_units_in_ascii = False

                # decode all strings (currently there will never be more than one per token)
                if 'S' in token_type.decode('ASCII'):
                    for i, _j in enumerate(raw_payload):
                        # raw payload may contain non-ASCII characters (i.e. filedate on non-English Windows OS)
                        payload[i] = raw_payload[i].decode('ASCII', 'replace').strip()
                else:
                    payload = raw_payload

                if payload_len == 1:
                    payload = payload[0]

                try:
                    token_name = SHBDOTagID(token_id).name
                    logger.debug("Read token {:s} (0x{:02x}) value {} type {:s} length {:d}".format(
                        token_name,
                        token_id,
                        raw_payload,
                        token_type.decode('ASCII'),
                        payload_len
                    ))
                except ValueError:
                    logger.info("Found unknown token (0x{:02x}) value {} type {:s} length {:d}, skipping".format(
                        token_id,
                        raw_payload,
                        token_type.decode('ASCII'),
                        payload_len
                    ))

                # geometry type
                if SHBDOTagID.geometry_type == token_id:
                    estimator.geotyp = SHGeoType[payload.strip().lower()]

                if SHBDOTagID.geo_n_bins == token_id:
                    estimator.x = estimator.x._replace(n=payload[0])
                    estimator.y = estimator.y._replace(n=payload[1])
                    estimator.z = estimator.z._replace(n=payload[2])

                if SHBDOTagID.geo_p_start == token_id:
                    estimator.x = estimator.x._replace(min_val=payload[0])
                    estimator.y = estimator.y._replace(min_val=payload[1])
                    estimator.z = estimator.z._replace(min_val=payload[2])

                if SHBDOTagID.geo_q_stop == token_id:
                    estimator.x = estimator.x._replace(max_val=payload[0])
                    estimator.y = estimator.y._replace(max_val=payload[1])
                    estimator.z = estimator.z._replace(max_val=payload[2])

                if SHBDOTagID.geo_unit_ids == token_id and not _has_geo_units_in_ascii:
                    estimator.x = estimator.x._replace(unit=unit_name_from_unit_id.get(payload[0], ""))
                    estimator.y = estimator.y._replace(unit=unit_name_from_unit_id.get(payload[1], ""))
                    estimator.z = estimator.z._replace(unit=unit_name_from_unit_id.get(payload[2], ""))

                # Units may also be given as pure ASCII directly from SHIELD-HIT12A new .bdo format.
                # If this is available, then use those embedded in the .bdo file, instead of pymchelper setting them.
                if SHBDOTagID.geo_units == token_id:
                    _units = payload.split(";")
                    if len(_units) == 3:
                        estimator.x = estimator.x._replace(unit=_units[0])
                        estimator.y = estimator.y._replace(unit=_units[1])
                        estimator.z = estimator.z._replace(unit=_units[2])
                        _has_geo_units_in_ascii = True

                # page(detector) type, it begins new page block
                if SHBDOTagID.detector_type == token_id:
                    # here new page is added to the estimator structure
                    estimator.add_page(Page())
                    logger.debug("Setting page.dettyp = {} ({})".format(SHDetType(payload), SHDetType(payload).name))
                    estimator.pages[-1].dettyp = SHDetType(payload)

                # page(detector) data is the last thing related to page that is saved in binary file
                # at this point all other page related tags should already be processed
                if SHBDOTagID.data_block == token_id:
                    logger.debug("Setting page data = {}".format(np.asarray(payload)))
                    estimator.pages[-1].data_raw = np.asarray(payload)

                # read tokens based on tag <-> name mapping for detector
                if token_id in detector_name_from_bdotag:
                    logger.debug("Setting detector.{} = {}".format(detector_name_from_bdotag[token_id], payload))
                    setattr(estimator, detector_name_from_bdotag[token_id], payload)

                # read tokens based on tag <-> name mapping for pages
                if token_id in page_tags_to_save:
                    logger.debug("Setting page.{} = {}".format(SHBDOTagID(token_id).name, payload))
                    setattr(estimator.pages[-1], SHBDOTagID(token_id).name, payload)

            # Loop over the file is over here
            # Check if we have differential scoring, i.e. data dimension is larger than 1:
            for page in estimator.pages:
                try:
                    page.diff_axis1 = MeshAxis(n=page.page_diff_size[0],
                                               min_val=page.page_diff_start[0],
                                               max_val=page.page_diff_stop[0],
                                               name="",
                                               unit=page.page_diff_units.split(";")[0],
                                               binning=MeshAxis.BinningType.linear)
                except AttributeError:
                    logger.info("Lack of data for first level differential scoring")
                except IndexError:
                    logger.info("Lack of units for first level differential scoring")

                try:
                    page.diff_axis2 = MeshAxis(n=page.page_diff_size[1],
                                               min_val=page.page_diff_start[1],
                                               max_val=page.page_diff_stop[1],
                                               name="",
                                               unit=page.page_diff_units.split(";")[1],
                                               binning=MeshAxis.BinningType.linear)
                except AttributeError:
                    logger.info("Lack of data for second level differential scoring")
                except IndexError:
                    logger.info("Lack of units for second level differential scoring")

            # Fix names of the axis objects for different mesh type,
            # units are directly extracted from BDO tags in 2019 format
            _, xname = mesh_unit_and_name(estimator, 0)
            _, yname = mesh_unit_and_name(estimator, 1)
            _, zname = mesh_unit_and_name(estimator, 2)
            estimator.x = estimator.x._replace(name=xname)
            estimator.y = estimator.y._replace(name=yname)
            estimator.z = estimator.z._replace(name=zname)

            # Copy the SH12A specific units into the general placeholders:
            for page in estimator.pages:
                page.unit = page.detector_unit
                # in future, a user may optionally give a more specific name in SH12A detect.dat, which then
                # may be written to the .bdo file. If the name is not set, use the official detector name instead:
                if not page.name:
                    page.name = str(page.dettyp)

            # apply basic normalization for pages with normalisation tag
            for page in estimator.pages:
                page_normalisation = getattr(page, 'page_normalized', None)
                # see pymchelper/readers/shieldhit/binary_spec.py for details on the normalisation tags
                # normalize the detectors such as dose or fluence (tagged as SH_POSTPROC_NORM or 2)
                if page_normalisation == 2:
                    page.data_raw /= np.float64(estimator.number_of_primaries)
                    page.error_raw /= np.float64(estimator.number_of_primaries)

        estimator.file_format = 'bdo2019'

        logger.debug("Done reading bdo file.")
        return True
