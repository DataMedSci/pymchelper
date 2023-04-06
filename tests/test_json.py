"""Tests for JSON converter"""
import logging
from pathlib import Path
import pytest

from pymchelper.input_output import fromfile
from pymchelper.axis import MeshAxis
from pymchelper.estimator import Estimator
from pymchelper.page import Page

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


def test_json_generation(manypage_bdo_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Check if JSON file can be generated from BDO."""
    # temporary change working directory
    monkeypatch.chdir(tmp_path)
    from pymchelper.run import main
    logger.debug("Parsing %s to JSON", manypage_bdo_path)
    main(['json', str(manypage_bdo_path)])

    expected_json_path = tmp_path / "ex_yzmsh.json"
    assert expected_json_path.exists()

    import json

    # check if JSON file can be read
    with open(expected_json_path, 'r') as reader:
        json_obj = json.load(reader)

        estimator_data: Estimator = fromfile(manypage_bdo_path)

        assert json_obj is not None
        for page_no, page in enumerate(estimator_data.pages):
            page: Page
            page_dict = json_obj["pages"][page_no]
            assert page.dimension == page_dict["dimensions"]
            assert page.unit == page_dict["data"]["unit"]
            assert page.name == page_dict["data"]["name"]
            if page.dimension == 0:
                assert len([page.data_raw.tolist()]) == len(page_dict["data"]["values"])
            else:
                assert len(page.data_raw.tolist()) == len(page_dict["data"]["values"])

            for i in range(page.dimension):
                axis: MeshAxis = page.plot_axis(i)
                assert str(axis.unit) == page_dict[f"{i+1}_axis"]["unit"]
                assert str(axis.name) == page_dict[f"{i+1}_axis"]["name"]
                assert len(axis.data.tolist()) == len(page_dict[f"{i+1}_axis"]["values"])
