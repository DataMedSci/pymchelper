"""Regression tests for SHIELD-HIT reader base helpers."""

import logging

import numpy as np
import pytest

from pymchelper.estimator import Estimator
from pymchelper.page import Page
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.readers.shieldhit.reader_base import _get_detector_unit, _postprocess, safe_dettyp


@pytest.mark.smoke
@pytest.mark.parametrize(("detector_id", "expected"), [
    (1, SHDetType.energy),
    (66, SHDetType.davge),
    (67, SHDetType.dbeta),
])
def test_safe_dettyp_known_id_roundtrips(detector_id, expected):
    """Convert known detector IDs into their enum members."""
    assert safe_dettyp(detector_id) == expected


@pytest.mark.smoke
def test_safe_dettyp_unknown_id_warns_and_falls_back_to_invalid(caplog):
    """Warn and fall back to invalid for unknown detector IDs."""
    with caplog.at_level(logging.WARNING):
        result = safe_dettyp(9999)

    assert result == SHDetType.invalid
    assert any("9999" in record.message for record in caplog.records)
    assert any(record.levelno == logging.WARNING for record in caplog.records)


@pytest.mark.smoke
def test_safe_dettyp_negative_id_warns_and_falls_back_to_invalid(caplog):
    """Warn and fall back to invalid for negative detector IDs."""
    with caplog.at_level(logging.WARNING):
        result = safe_dettyp(-1)

    assert result == SHDetType.invalid


@pytest.mark.smoke
def test_averaged_detector_units_are_defined():
    """Expose explicit units and names for averaged kinetic-energy, beta, and Q_eff scorers."""
    assert _get_detector_unit(SHDetType.davge, None) == ("MeV/nucleon", "Dose-averaged kinetic energy")
    assert _get_detector_unit(SHDetType.dbeta, None) == ("(dimensionless)", "Dose-averaged beta")
    assert _get_detector_unit(SHDetType.dq_eff, None) == ("(nil)", "Dose-averaged Q_eff")
    assert _get_detector_unit(SHDetType.tq_eff, None) == ("(nil)", "Track-averaged Q_eff")


@pytest.mark.smoke
def test_tavge_tbeta_resolve_via_avg_energy_avg_beta_aliases():
    """Resolve openshieldhit aliases through the existing average-energy and average-beta entries."""
    assert _get_detector_unit(SHDetType.tavge, None) == _get_detector_unit(SHDetType.avg_energy, None)
    assert _get_detector_unit(SHDetType.tbeta, None) == _get_detector_unit(SHDetType.avg_beta, None)


@pytest.mark.smoke
@pytest.mark.parametrize("dettyp", [SHDetType.dq_eff, SHDetType.tq_eff])
def test_postprocess_skips_normalization_for_averaged_q_eff(dettyp):
    """Preserve already averaged Q_eff scorers during per-primary postprocessing."""
    estimator = Estimator()
    estimator.number_of_primaries = 10
    page = Page()
    page.dettyp = dettyp
    page.data_raw = np.array([5.0])
    estimator.add_page(page)

    _postprocess(estimator, nscale=1)

    np.testing.assert_array_equal(estimator.pages[0].data_raw, np.array([5.0]))
