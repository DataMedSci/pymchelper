"""Tests for HDF converter"""
import logging
from pathlib import Path
from typing import List
from pymchelper.input_output import fromfile
import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def manypage_bdo_path() -> Path:
    """Location of this script according to pathlib"""
    main_dir = Path(__file__).resolve().parent
    return main_dir / "res" / "shieldhit" / "v1.0.0" / "ex_yzmsh.bdo"


def test_output_basic_properties(manypage_bdo_path: Path):
    """Check if test file exists."""
    assert manypage_bdo_path.exists()
    assert manypage_bdo_path.is_file()
    assert manypage_bdo_path.stat().st_size > 0


def test_bdo_reading(manypage_bdo_path: Path):
    """Check parsing of the multipage BDO."""
    estimator_data = fromfile(manypage_bdo_path)
    assert estimator_data is not None
    assert estimator_data.pages is not None
    assert len(estimator_data.pages) == 3
    assert estimator_data.pages[0].data is not None


def test_hdf_generation(manypage_bdo_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Check if HDF file can be generated from BDO."""
    # temporary change working directory
    monkeypatch.chdir(tmp_path)
    from pymchelper.run import main
    logger.debug("Parsing %s to HDF", manypage_bdo_path)
    main(['hdf', str(manypage_bdo_path)])

    expected_hdf_path = tmp_path / "ex_yzmsh.h5"
    assert expected_hdf_path.exists()

    import h5py

    # check if HDF file can be read
    with h5py.File(expected_hdf_path, 'r') as hf:

        estimator_data = fromfile(manypage_bdo_path)

        assert hf is not None
        assert hf.attrs is not None
        for page_no, page in enumerate(estimator_data.pages):
            assert hf[f"data_{page_no}"] is not None
            assert hf[f"data_{page_no}"].attrs is not None
            assert hf[f"data_{page_no}"].attrs["name"] == page.name
            assert hf[f"data_{page_no}"].attrs["unit"] == page.unit
            assert hf[f"data_{page_no}"].attrs["nstat"] == estimator_data.number_of_primaries
            assert hf[f"data_{page_no}"].attrs["counter"] == estimator_data.file_counter
            assert hf[f"data_{page_no}"].attrs["xaxis_n"] == page.x.n
            assert hf[f"data_{page_no}"].attrs["xaxis_min"] == page.x.min_val
            assert hf[f"data_{page_no}"].attrs["xaxis_max"] == page.x.max_val
            assert hf[f"data_{page_no}"].attrs["yaxis_n"] == page.y.n
            assert hf[f"data_{page_no}"].attrs["yaxis_min"] == page.y.min_val
            assert hf[f"data_{page_no}"].attrs["yaxis_max"] == page.y.max_val
            assert hf[f"data_{page_no}"].attrs["zaxis_n"] == page.z.n
            assert hf[f"data_{page_no}"].attrs["zaxis_min"] == page.z.min_val
            assert hf[f"data_{page_no}"].attrs["zaxis_max"] == page.z.max_val
            assert hf[f"data_{page_no}"].attrs["xaxis_name"] == page.x.name
            assert hf[f"data_{page_no}"].attrs["yaxis_name"] == page.y.name
            assert hf[f"data_{page_no}"].attrs["zaxis_name"] == page.z.name
            assert hf[f"data_{page_no}"].attrs["xaxis_unit"] == page.x.unit
            assert hf[f"data_{page_no}"].attrs["yaxis_unit"] == page.y.unit
            assert hf[f"data_{page_no}"].attrs["zaxis_unit"] == page.z.unit
            # check if data is the same
            assert hf[f"data_{page_no}"].shape == page.data.shape
            assert hf[f"data_{page_no}"][:] == pytest.approx(page.data)
