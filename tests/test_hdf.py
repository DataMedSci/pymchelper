"""Tests for HDF converter"""
import logging
import os
from pathlib import Path
import enum
from typing import List
from pymchelper.input_output import fromfile
import pymchelper.utils.mcscripter
import pytest

logger = logging.getLogger(__name__)

@pytest.fixture(scope='module')
def manypage_bdo_path() -> Path:
    """Location of this script according to pathlib"""
    main_dir = Path(__file__).resolve().parent
    return main_dir / "res" / "shieldhit" / "v1.0.0" / "ex_yzmsh.bdo"    


def test_output_basic_properties(manypage_bdo_path : Path):
    """Check if test file exists."""
    assert manypage_bdo_path.exists()
    assert manypage_bdo_path.is_file()
    assert manypage_bdo_path.stat().st_size > 0


def test_bdo_reading(manypage_bdo_path : Path):
    """Check parsing of the multipage BDO."""
    estimator_data = fromfile(manypage_bdo_path)
    assert estimator_data is not None
    assert estimator_data.pages is not None
    assert len(estimator_data.pages) == 3
    assert estimator_data.pages[0].data is not None    


def test_hdf_generation(manypage_bdo_path : Path, tmp_path : Path, monkeypatch: pytest.MonkeyPatch):
    """Check if HDF file can be generated from BDO."""
    # temporary change working directory
    monkeypatch.chdir(tmp_path)
    from pymchelper.run import main
    logger.info(f"Parsing {manypage_bdo_path} to HDF")
    main(['hdf', str(manypage_bdo_path)])
    assert Path('ex_yzmsh.h5').exists()

