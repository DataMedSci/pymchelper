"""Tests for inspect converter"""
from pathlib import Path

import pytest

from pymchelper import run

shieldhit_dir = Path(__file__).resolve().parent / "res" / "shieldhit"


@pytest.mark.parametrize("file_path, expected_scatter_plots, expected_histograms", [
    (shieldhit_dir / "generated" / "many" / "cyl" / "aen_0_al0001.bdo", 0, 0),
    (shieldhit_dir / "single" / "ex_zmsh.bdo", 1, 1),
    (shieldhit_dir / "v1.0.0" / "ex_yzmsh.bdo", 0, 3),
])
def test_inspect_details(file_path: Path, expected_scatter_plots: int, expected_histograms: int,
                         capsys: pytest.CaptureFixture):
    """inspect --details plots every page: scatter plot for 1D pages, histogram for pages with more than one value"""
    pytest.importorskip("hipsterplot")
    pytest.importorskip("bashplotlib")

    status = run.main(["inspect", "--details", str(file_path)])

    output = capsys.readouterr().out
    assert status == 0
    assert output.count("data scatter plot") == expected_scatter_plots
    assert output.count("data histogram") == expected_histograms
