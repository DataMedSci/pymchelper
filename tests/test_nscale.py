"""Tests for scaling per-primary results to a number of particles given with convertmc --nscale"""
import json
import logging
from pathlib import Path

import numpy as np
import pytest

from pymchelper.estimator import Estimator
from pymchelper.input_output import fromfile, fromfilelist
from pymchelper.page import Page
from pymchelper.readers.shieldhit.reader_base import scale_to_particles
from pymchelper.run import main
from pymchelper.shieldhit.detector.detector_type import SHDetType

# 1 megaelectron volt / gram = 1.60217662 x 10-10 Gy
MeV_g = 1.60217662e-10


@pytest.fixture(scope='module')
def averaging_dir(main_dir: Path) -> Path:
    """Directory with three SHIELD-HIT12A runs of DOSE and FLUENCE in BDO2019 format"""
    return main_dir / "res" / "shieldhit" / "averaging"


def test_merged_dose_and_fluence_scaled_once_with_errors(averaging_dir: Path):
    """Dose is scaled to Gy of nscale particles, fluence to nscale particles, errors the same as data."""
    files = sorted(str(path) for path in averaging_dir.glob("normalisation-5_aggregation-mean_000*.bdo"))
    per_primary = fromfilelist(files)
    scaled = fromfilelist(files)
    nscale = 1e8

    scale_to_particles(scaled, nscale)

    dose_per_primary = per_primary.pages[0]
    dose_scaled = scaled.pages[0]
    assert dose_scaled.dettyp == SHDetType.dose_gy_bdo2016
    assert dose_scaled.unit == "Gy"
    np.testing.assert_allclose(dose_scaled.data_raw, dose_per_primary.data_raw * nscale * MeV_g, rtol=1e-12)
    np.testing.assert_allclose(dose_scaled.error_raw, dose_per_primary.error_raw * nscale * MeV_g, rtol=1e-12)

    fluence_per_primary = per_primary.pages[1]
    fluence_scaled = scaled.pages[1]
    assert fluence_per_primary.unit == "/cm^2/prim"
    assert fluence_scaled.unit == "/cm^2"
    np.testing.assert_allclose(fluence_scaled.data_raw, fluence_per_primary.data_raw * nscale, rtol=1e-12)
    np.testing.assert_allclose(fluence_scaled.error_raw, fluence_per_primary.error_raw * nscale, rtol=1e-12)


def test_scaling_twice_has_no_effect(averaging_dir: Path):
    """A page is scaled only once, calling scale_to_particles again leaves it as it is."""
    estimator = fromfile(str(averaging_dir / "normalisation-5_aggregation-mean_0001.bdo"))
    scale_to_particles(estimator, 10)
    fluence_after_first_call = estimator.pages[1].data_raw.copy()

    scale_to_particles(estimator, 10)

    np.testing.assert_array_equal(estimator.pages[1].data_raw, fluence_after_first_call)


def test_averaged_pages_not_scaled(main_dir: Path):
    """LET and zone pages are not normalised per primary, so nscale leaves them unchanged."""
    path = str(main_dir / "res" / "shieldhit" / "v1.0.0" / "ex_yzmsh.bdo")
    per_primary = fromfile(path)
    scaled = fromfile(path)

    scale_to_particles(scaled, 1000)

    for page_per_primary, page_scaled in zip(per_primary.pages[1:], scaled.pages[1:]):
        assert page_scaled.unit == page_per_primary.unit
        np.testing.assert_array_equal(page_scaled.data_raw, page_per_primary.data_raw)


def test_bin2010_energy_scaled(main_dir: Path):
    """bin2010 energy page in MeV/primary becomes MeV of nscale particles."""
    path = str(main_dir / "res" / "shieldhit" / "single" / "ex_cyl.bdo")
    per_primary = fromfile(path)
    scaled = fromfile(path)

    scale_to_particles(scaled, 1000)

    assert scaled.pages[0].unit == "MeV"
    np.testing.assert_allclose(scaled.pages[0].data_raw, per_primary.pages[0].data_raw * 1000, rtol=1e-12)


def test_warning_when_nothing_is_per_primary(caplog: pytest.LogCaptureFixture):
    """Estimator without pages normalised per primary (e.g. FLUKA) stays unchanged and a warning is logged."""
    estimator = Estimator()
    page = Page()
    page.data_raw = np.array([5.0])
    estimator.add_page(page)

    with caplog.at_level(logging.WARNING):
        scale_to_particles(estimator, 1000)

    np.testing.assert_array_equal(estimator.pages[0].data_raw, np.array([5.0]))
    assert "nscale has no effect" in caplog.text


def test_convertmc_nscale(averaging_dir: Path, tmp_path: Path):
    """convertmc json -n writes dose in Gy of nscale particles."""
    path = str(averaging_dir / "normalisation-5_aggregation-mean_0001.bdo")
    output_per_primary = tmp_path / "per_primary.json"
    output_scaled = tmp_path / "scaled.json"

    status_per_primary = main(["json", path, str(output_per_primary)])
    status_scaled = main(["json", "-n", "1000", path, str(output_scaled)])

    assert status_per_primary == 0
    assert status_scaled == 0
    with open(output_per_primary) as reader:
        dose_per_primary = json.load(reader)["pages"][0]["data"]
    with open(output_scaled) as reader:
        dose_scaled = json.load(reader)["pages"][0]["data"]
    assert dose_per_primary["unit"] == "MeV/g/prim"
    assert dose_scaled["unit"] == "Gy"
    np.testing.assert_allclose(dose_scaled["values"], np.array(dose_per_primary["values"]) * 1000 * MeV_g, rtol=1e-12)
