"""Tests for MCPL converter"""
import logging
from pathlib import Path
from typing import Generator
import numpy as np
from pymchelper.estimator import ErrorEstimate
from pymchelper.input_output import fromfile, fromfilelist
import pytest
import mcpl

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def phasespace_bdo_file_path() -> Generator[Path, None, None]:
    """Location of this script according to pathlib"""
    main_dir = Path(__file__).resolve().parent
    yield main_dir / "res" / "shieldhit" / "phasespace" / "NB_mcpl.bdo"


@pytest.fixture(scope='function')
def phasespace_bdo_files_path() -> Generator[Path, None, None]:
    """Location of this script according to pathlib"""
    main_dir = Path(__file__).resolve().parent
    return (main_dir / "res" / "shieldhit" / "phasespace").glob("NB_mcpl_000*.bdo")


def test_output_basic_properties(phasespace_bdo_file_path: Path, phasespace_bdo_files_path: Generator[Path, None,
                                                                                                      None]):
    """Check if test file exists."""
    logging.info("Testing if %s is regular file", phasespace_bdo_file_path)
    assert phasespace_bdo_file_path.exists()
    assert phasespace_bdo_file_path.is_file()
    assert phasespace_bdo_file_path.stat().st_size > 0

    for file in phasespace_bdo_files_path:
        logging.info("Testing if %s is regular file", file)
        assert file.exists()
        assert file.is_file()
        assert file.stat().st_size > 0


def test_bdo_reading(phasespace_bdo_file_path: Path):
    """Check parsing of the multipage BDO."""
    logging.info("Checking if parsing works for %s", phasespace_bdo_file_path)
    estimator_data = fromfile(str(phasespace_bdo_file_path))
    assert estimator_data is not None
    assert estimator_data.pages is not None
    assert estimator_data.dimension == 0
    assert estimator_data.error_type == ErrorEstimate.none
    for i in range(3):
        axis_data = estimator_data.axis(i)
        assert axis_data is not None
        assert axis_data.n == 1
    assert len(estimator_data.pages) == 3
    assert estimator_data.pages[0].data is not None
    assert estimator_data.pages[0].data.shape == (8, 11)


def test_bdo_properly_read(phasespace_bdo_file_path: Path):
    """Check if the data is properly read."""
    logging.info("Checking if data is properly read for %s", phasespace_bdo_file_path)
    estimator_data = fromfile(str(phasespace_bdo_file_path))
    assert estimator_data is not None
    mcpl_as_text_path = phasespace_bdo_file_path.with_suffix(".txt")
    assert mcpl_as_text_path.exists()
    assert mcpl_as_text_path.is_file()
    assert mcpl_as_text_path.stat().st_size > 0

    txt_data = np.loadtxt(mcpl_as_text_path)
    assert txt_data is not None
    assert txt_data.shape == (25, 8)

    list_of_arrays = [page.data for page in estimator_data.pages]
    # concatenate all pages into one numpy array
    all_pages = np.concatenate(list_of_arrays, axis=1)
    assert all_pages is not None
    assert all_pages.shape == (8, 25)

    assert np.allclose(txt_data, all_pages.T)


def test_mcpl_generation(phasespace_bdo_file_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Check if MCPL file can be generated from BDO."""
    logging.info("Checking if MCPL file can be generated from BDO %s", phasespace_bdo_file_path)
    # temporary change working directory
    from pymchelper.run import main
    logging.info("Changing working directory to %s", tmp_path)
    monkeypatch.chdir(tmp_path)
    main(['mcpl', str(phasespace_bdo_file_path)])

    estimator_data = fromfile(str(phasespace_bdo_file_path))

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


def test_concatenation_of_bdo_files(phasespace_bdo_files_path: Generator[Path, None, None]):
    """Check if concatenation of BDO files works."""
    list_of_input_files = list(phasespace_bdo_files_path)
    logging.info("Checking if concatenation of BDO files works for %s", list_of_input_files)
    assert len(list_of_input_files) == 3

    estimator_data = fromfilelist(list_of_input_files)
    assert estimator_data is not None
