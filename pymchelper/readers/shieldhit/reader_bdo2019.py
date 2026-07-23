import logging

import numpy as np

from pymchelper.axis import MeshAxis
from pymchelper.page import Page
from pymchelper.readers.shieldhit.binary_spec import SHBDOTagID, detector_name_from_bdotag, unit_name_from_unit_id, \
    page_tags_to_save
from pymchelper.readers.shieldhit.reader_base import SHReader, read_next_token, mesh_unit_and_name, safe_dettyp
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

logger = logging.getLogger(__name__)


class SHReaderBDO2019(SHReader):
    """Experimental binary format reader version >= 0.7"""

    def read_data(self, estimator, nscale=1):
        logger.debug("Reading: %s", self.filename)

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
                _process_token(estimator, token)

            _finalize_estimator(estimator)

        estimator.file_format = 'bdo2019'
        estimator.data_order = 'F'  # Fortran column-major order

        logger.debug("Done reading bdo file.")
        return True


def _decode_payload(token):
    """Decode a raw token into its final Python/numpy payload representation."""
    token_id, token_type, payload_len, raw_payload = token

    payload = [None] * payload_len

    # decode all strings (currently there will never be more than one per token)
    if 'S' in token_type.decode('ASCII'):
        for i, payload_entry in enumerate(raw_payload):
            # raw payload may contain non-ASCII characters (i.e. filedate on non-English Windows OS)
            payload[i] = payload_entry.decode('ASCII', 'replace').strip()
    else:
        payload = raw_payload

    if payload_len == 1:
        payload = payload[0]

    try:
        token_name = SHBDOTagID(token_id).name
        logger.debug("Read token {:s} (0x{:02x}) value {} type {:s} length {:d}".format(
            token_name, token_id, raw_payload, token_type.decode('ASCII'), payload_len))
    except ValueError:
        logger.info("Found unknown token (0x{:02x}) value {} type {:s} length {:d}, skipping".format(
            token_id, raw_payload, token_type.decode('ASCII'), payload_len))

    return payload


def _process_token(estimator, token):
    """Apply a single decoded BDO token to the estimator (and its current page) being built."""
    token_id = token[0]
    payload = _decode_payload(token)

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

    if SHBDOTagID.geo_unit_ids == token_id:
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

    # page(detector) type, it begins new page block
    if SHBDOTagID.detector_type == token_id:
        # here new page is added to the estimator structure
        estimator.add_page(Page())
        dettyp = safe_dettyp(payload)
        logger.debug("Setting page.dettyp = %s (%s)", dettyp, dettyp.name)
        estimator.pages[-1].dettyp = dettyp

    # page(detector) data is the last thing related to page that is saved in binary file
    # at this point all other page related tags should already be processed
    if SHBDOTagID.data_block == token_id:
        logger.debug("Setting page data = %s", np.asarray(payload))
        estimator.pages[-1].data_raw = np.asarray(payload)

    # read tokens based on tag <-> name mapping for detector
    if token_id in detector_name_from_bdotag:
        logger.debug("Setting detector.%s = %s", detector_name_from_bdotag[token_id], payload)
        setattr(estimator, detector_name_from_bdotag[token_id], payload)

    # read tokens based on tag <-> name mapping for pages
    if token_id in page_tags_to_save:
        logger.debug("Setting page.%s = %s", SHBDOTagID(token_id).name, payload)
        setattr(estimator.pages[-1], SHBDOTagID(token_id).name, payload)


def _diff_axis_binning(diff_flag, index):
    """
    Determine the binning type of a differential axis from the raw page_diff_flag tag.

    page_diff_flag holds, for each differential axis, 1 if binning is linear
    and -1 if binning is logarithmic (i.e. log10 was requested in detect.dat).
    The tag may be absent, a scalar, or an array shorter than expected, so any
    of those cases are treated as "flag not available" and default to linear.

    :param diff_flag: raw payload of the page_diff_flag tag, or None if absent
    :param index: 0 for the first differential axis, 1 for the second
    :return: MeshAxis.BinningType.linear or MeshAxis.BinningType.logarithmic
    """
    if diff_flag is None:
        return MeshAxis.BinningType.linear

    flags = np.atleast_1d(diff_flag)
    if index >= flags.size:
        return MeshAxis.BinningType.linear

    return MeshAxis.BinningType.logarithmic if flags[index] < 0 else MeshAxis.BinningType.linear


def _set_diff_axes(page):
    """Populate page.diff_axis1 and page.diff_axis2, if differential scoring data is present."""
    diff_flag = getattr(page, 'page_diff_flag', None)

    try:
        try:
            first_axis_unit = page.page_diff_units.split(";")[0]
        except IndexError:
            first_axis_unit = ""
        page.diff_axis1 = MeshAxis(n=page.page_diff_size[0],
                                   min_val=page.page_diff_start[0],
                                   max_val=page.page_diff_stop[0],
                                   name="",
                                   unit=first_axis_unit,
                                   binning=_diff_axis_binning(diff_flag, 0))
    except AttributeError:
        logger.debug("Lack of data for first level differential scoring")

    try:
        try:
            second_axis_unit = page.page_diff_units.split(";")[1]
        except IndexError:
            second_axis_unit = ""
        page.diff_axis2 = MeshAxis(n=page.page_diff_size[1],
                                   min_val=page.page_diff_start[1],
                                   max_val=page.page_diff_stop[1],
                                   name="",
                                   unit=second_axis_unit,
                                   binning=_diff_axis_binning(diff_flag, 1))
    except AttributeError:
        logger.debug("Lack of data for second level differential scoring")


def _finalize_estimator(estimator):
    """Post-process an estimator once all BDO tokens have been read."""
    # Check if we have differential scoring, i.e. data dimension is larger than 1:
    for page in estimator.pages:
        _set_diff_axes(page)

    # Special treatment for MCPL detector
    for page in estimator.pages:
        if page.dettyp == SHDetType.mcpl:
            estimator.dim = 0

    # Fix names of the axis objects for different mesh type,
    # units are directly extracted from BDO tags in 2019 format
    _, xname = mesh_unit_and_name(estimator, 0)
    _, yname = mesh_unit_and_name(estimator, 1)
    _, zname = mesh_unit_and_name(estimator, 2)
    estimator.x = estimator.x._replace(name=xname)
    estimator.y = estimator.y._replace(name=yname)
    estimator.z = estimator.z._replace(name=zname)

    for page in estimator.pages:
        # Copy the SH12A specific units into the general placeholders:
        page.unit = page.detector_unit
        # in future, a user may optionally give a more specific name in SH12A detect.dat, which then
        # may be written to the .bdo file. If the name is not set, use the official detector name instead:
        if not page.name:
            page.name = str(page.dettyp)

        # apply basic normalization for pages with normalisation tag
        page_normalisation = getattr(page, 'page_normalized', None)
        # see pymchelper/readers/shieldhit/binary_spec.py for details on the normalisation tags
        # normalize the detectors such as dose or fluence (tagged as SH_POSTPROC_NORM or 2)
        if page_normalisation == 2:
            page.data_raw /= np.float64(estimator.number_of_primaries)
            page.unit += "/prim"
