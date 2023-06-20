"""Tests for MCPL converter"""
import logging
from pathlib import Path
from typing import Generator
import numpy as np
from pymchelper.estimator import ErrorEstimate
from pymchelper.input_output import fromfile
import pytest
import mcpl

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def manypage_bdo_path() -> Generator[Path, None, None]:
    """Location of this script according to pathlib"""
    main_dir = Path(__file__).resolve().parent
    yield main_dir / "res" / "shieldhit" / "phasespace" / "NB_mcpl.bdo"


def test_output_basic_properties(manypage_bdo_path: Path):
    """Check if test file exists."""
    assert manypage_bdo_path.exists()
    assert manypage_bdo_path.is_file()
    assert manypage_bdo_path.stat().st_size > 0


def test_bdo_reading(manypage_bdo_path: Path):
    """Check parsing of the multipage BDO."""
    estimator_data = fromfile(str(manypage_bdo_path))
    assert estimator_data is not None
    assert estimator_data.pages is not None
    assert estimator_data.dim == 0
    assert estimator_data.error_type == ErrorEstimate.none
    for i in range(3):
        assert estimator_data.axis(i).n == 1
    assert len(estimator_data.pages) == 3
    assert estimator_data.pages[0].data is not None
    assert estimator_data.pages[0].data.shape == (8, 10)
    print(estimator_data.pages[0].data)


def test_bdo_properly_read(manypage_bdo_path: Path):
    """Check if the data is properly read."""
    estimator_data = fromfile(str(manypage_bdo_path))
    assert estimator_data is not None
    mcpl_as_text_path = manypage_bdo_path.with_suffix(".txt")
    assert mcpl_as_text_path.exists()
    assert mcpl_as_text_path.is_file()
    assert mcpl_as_text_path.stat().st_size > 0

    txt_data = np.loadtxt(mcpl_as_text_path)
    assert txt_data is not None
    assert txt_data.shape == (27, 8)

    list_of_arrays = [page.data for page in estimator_data.pages]
    # concatenate all pages into one numpy array
    all_pages = np.concatenate(list_of_arrays, axis=1)
    assert all_pages is not None
    assert all_pages.shape == (8, 27)

    assert np.allclose(txt_data, all_pages.T)


def test_mcpl_generation(manypage_bdo_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Check if MCPL file can be generated from BDO."""
    # temporary change working directory
    monkeypatch.chdir(tmp_path)
    from pymchelper.run import main
    logger.debug("Parsing %s to MCPL", manypage_bdo_path)
    main(['mcpl', str(manypage_bdo_path)])

    estimator_data = fromfile(str(manypage_bdo_path))

    assert estimator_data is not None

    for i, page in enumerate(estimator_data.pages):
        expected_mcpl_path = tmp_path / f'NB_mcpl_p{i+1}.mcpl'
        assert expected_mcpl_path.exists()
        assert expected_mcpl_path.is_file()
        assert expected_mcpl_path.stat().st_size > 0

        mcpl_file = mcpl.MCPLFile(expected_mcpl_path)
        assert mcpl_file is not None
        assert mcpl_file.nparticles == page.data.shape[1]
        for p in mcpl_file.particles:
            assert p.weight == 1.0
            assert p.pdgcode == 2212  # protons
            assert p.position[2] == 4.0
