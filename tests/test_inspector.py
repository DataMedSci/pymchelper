"""Tests for inspect converter"""
from pathlib import Path

import pytest

from pymchelper import run

shieldhit_dir = Path(__file__).resolve().parent / "res" / "shieldhit"


@pytest.mark.parametrize("file_path", [
    shieldhit_dir / "single" / "ex_zmsh.bdo",
    shieldhit_dir / "single" / "ex_yzmsh.bdo",
    shieldhit_dir / "v1.0.0" / "ex_yzmsh.bdo",
])
def test_inspect_details(file_path: Path, capsys: pytest.CaptureFixture):
    """inspect --details plots every page: scatter plot for 1D pages, histogram for all"""
    pytest.importorskip("hipsterplot")
    pytest.importorskip("bashplotlib")

    status = run.main(["inspect", "--details", str(file_path)])

    output = capsys.readouterr().out
    assert status == 0
    number_of_pages = output.count("Data min:")
    assert output.count("data histogram") == number_of_pages
    if file_path.name == "ex_zmsh.bdo":
        assert output.count("data scatter plot") == number_of_pages
    else:
        assert output.count("data scatter plot") == 0
