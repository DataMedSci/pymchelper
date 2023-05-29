"""Tests for MCPL converter"""
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
    yield main_dir / "res" / "shieldhit" / "phasespace" / "NB_mcpl.bdo"


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


# def test_hdf_generation(manypage_bdo_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
#     """Check if HDF file can be generated from BDO."""
#     # temporary change working directory
#     monkeypatch.chdir(tmp_path)
#     from pymchelper.run import main
#     logger.debug("Parsing %s to HDF", manypage_bdo_path)
#     main(['hdf', str(manypage_bdo_path)])

#     expected_hdf_path = tmp_path / "ex_yzmsh.h5"
#     assert expected_hdf_path.exists()

#     import h5py

#     # check if HDF file can be read
#     with h5py.File(expected_hdf_path, 'r') as hf:

#         estimator_data = fromfile(manypage_bdo_path)

#         assert hf is not None
#         assert hf.attrs is not None
#         for page_no, page in enumerate(estimator_data.pages):
#             assert hf[f"data_{page_no}"] is not None
#             assert hf[f"data_{page_no}"].attrs is not None
#             assert hf[f"data_{page_no}"].attrs["name"] == page.name
#             assert hf[f"data_{page_no}"].attrs["unit"] == page.unit
#             assert hf[f"data_{page_no}"].attrs["nstat"] == estimator_data.number_of_primaries
#             assert hf[f"data_{page_no}"].attrs["counter"] == estimator_data.file_counter
#             assert hf[f"data_{page_no}"].attrs["xaxis_n"] == estimator_data.x.n
#             assert hf[f"data_{page_no}"].attrs["xaxis_min"] == estimator_data.x.min_val
#             assert hf[f"data_{page_no}"].attrs["xaxis_max"] == estimator_data.x.max_val
#             assert hf[f"data_{page_no}"].attrs["yaxis_n"] == estimator_data.y.n
#             assert hf[f"data_{page_no}"].attrs["yaxis_min"] == estimator_data.y.min_val
#             assert hf[f"data_{page_no}"].attrs["yaxis_max"] == estimator_data.y.max_val
#             assert hf[f"data_{page_no}"].attrs["zaxis_n"] == estimator_data.z.n
#             assert hf[f"data_{page_no}"].attrs["zaxis_min"] == estimator_data.z.min_val
#             assert hf[f"data_{page_no}"].attrs["zaxis_max"] == estimator_data.z.max_val
#             assert hf[f"data_{page_no}"].attrs["xaxis_name"] == estimator_data.x.name
#             assert hf[f"data_{page_no}"].attrs["yaxis_name"] == estimator_data.y.name
#             assert hf[f"data_{page_no}"].attrs["zaxis_name"] == estimator_data.z.name
#             assert hf[f"data_{page_no}"].attrs["xaxis_unit"] == estimator_data.x.unit
#             assert hf[f"data_{page_no}"].attrs["yaxis_unit"] == estimator_data.y.unit
#             assert hf[f"data_{page_no}"].attrs["zaxis_unit"] == estimator_data.z.unit
#             # check if data is the same
#             assert hf[f"data_{page_no}"].shape == page.data.shape
#             assert hf[f"data_{page_no}"][:] == pytest.approx(page.data)
