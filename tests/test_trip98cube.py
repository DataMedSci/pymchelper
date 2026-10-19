"""Tests for tripcube converter"""
from pathlib import Path

import numpy as np
import pytest

from pymchelper.estimator import Estimator
from pymchelper.input_output import fromfile, tofile
from pymchelper.shieldhit.detector.detector_type import SHDetType

# BDO2019 file with DOSE (page 0) and TLET (page 1) on a 1 x 100 x 300 YZ mesh
yz_mesh_file = Path(__file__).resolve().parent / "res" / "shieldhit" / "v1.0.0" / "ex_yzmsh.bdo"


def single_page_estimator(page_number: int) -> Estimator:
    """Estimator from `yz_mesh_file` with only one page kept, the writer accepts single page estimators only"""
    estimator = fromfile(str(yz_mesh_file))
    estimator.pages = estimator.pages[page_number:page_number + 1]
    return estimator


def test_dose_cube(tmp_path: Path):
    """DOSE page is written as (z, y, x) cube scaled to 1200 at maximum, BDO2019 has no TRiP98 normalisation"""
    pytest.importorskip("pytrip")
    from pytrip import dos

    estimator = single_page_estimator(page_number=0)
    page = estimator.pages[0]
    assert page.dettyp == SHDetType.dose

    tofile(estimator, str(tmp_path / "dose"), "tripcube", None)

    cube = dos.DosCube()
    cube.read(str(tmp_path / "dose.dos"))
    page_data_zyx = page.data[:, :, :, 0, 0].transpose()
    expected = page_data_zyx / page_data_zyx.max() * 1200.0
    assert cube.cube.shape == (300, 100, 1)
    # cube is saved as 16-bit integers
    np.testing.assert_allclose(cube.cube, expected, atol=1.0)


def test_dose_cube_with_trip_normalisation(tmp_path: Path):
    """DOSE page is scaled with planned dose and number of particles when the file carries them"""
    pytest.importorskip("pytrip")
    from pytrip import dos

    estimator = single_page_estimator(page_number=0)
    page = estimator.pages[0]
    estimator.tripdose = 2.0
    estimator.tripntot = 10**9

    tofile(estimator, str(tmp_path / "dose"), "tripcube", None)

    cube = dos.DosCube()
    cube.read(str(tmp_path / "dose.dos"))
    page_data_zyx = page.data[:, :, :, 0, 0].transpose()
    expected = page_data_zyx * estimator.tripntot * 1.602e-10 / estimator.tripdose * 1000.0
    np.testing.assert_allclose(cube.cube, expected, atol=1.0)


def test_let_cube(tmp_path: Path):
    """TLET page is written as (z, y, x) cube in keV/um, page data stays in MeV/cm"""
    pytest.importorskip("pytrip")
    from pytrip import let

    estimator = single_page_estimator(page_number=1)
    page = estimator.pages[0]
    assert page.dettyp == SHDetType.tlet
    page_data_before = page.data_raw.copy()

    tofile(estimator, str(tmp_path / "let"), "tripcube", None)

    cube = let.LETCube()
    cube.read(str(tmp_path / "let.dos"))
    page_data_zyx = page.data[:, :, :, 0, 0].transpose()
    assert cube.cube.shape == (300, 100, 1)
    np.testing.assert_allclose(cube.cube, page_data_zyx * 0.1, rtol=1e-6)
    np.testing.assert_array_equal(page.data_raw, page_data_before)
