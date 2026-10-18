"""Writers put every value on its own bin, whatever the memory order of the input format"""
import argparse
import json
from pathlib import Path

import numpy as np
import pytest

from pymchelper.input_output import fromfile, tofile
from pymchelper.writers.fortranformatter import format_e
from pymchelper.writers.shieldhit import _format_e_fast

res_dir = Path(__file__).resolve().parent / "res" / "shieldhit"
mesh_2d_files = [
    str(res_dir / "v1.0.0" / "ex_yzmsh.bdo"),  # BDO2019, data_order 'F'
    str(res_dir / "single" / "ex_yzmsh.bdo"),  # bin2010, data_order 'C'
]


@pytest.mark.parametrize("path", mesh_2d_files, ids=["bdo2019", "bin2010"])
def test_json_values(path: str, tmp_path: Path):
    """JSON values walk the bins with the first axis fastest"""
    estimator = fromfile(path)
    tofile(estimator, str(tmp_path / "out"), "json", None)
    page_dict = json.loads((tmp_path / "out.json").read_text())["pages"][0]
    n1, n2 = len(page_dict["axis_dim1"]["values"]), len(page_dict["axis_dim2"]["values"])

    values = np.array(page_dict["data"]["values"]).reshape(n2, n1).T
    np.testing.assert_array_equal(values, np.squeeze(estimator.pages[0].data))


@pytest.mark.parametrize("path", mesh_2d_files, ids=["bdo2019", "bin2010"])
def test_txt_rows(path: str, tmp_path: Path):
    """Each txt row holds the value of the bin at its coordinates"""
    estimator = fromfile(path)
    estimator.pages = estimator.pages[:1]
    page = estimator.pages[0]
    tofile(estimator, str(tmp_path / "out"), "txt", None)
    rows = np.loadtxt(tmp_path / "out.txt")

    idx = [np.abs(page.axis(i).data[None] - rows[:, [i]]).argmin(axis=1) for i in range(3)]
    np.testing.assert_allclose(rows[:, 3], page.data[idx[0], idx[1], idx[2], 0, 0], rtol=1e-15)


@pytest.mark.parametrize("path", mesh_2d_files, ids=["bdo2019", "bin2010"])
def test_image_pixels(path: str):
    """The 2D map has the vertical axis along rows"""
    pytest.importorskip("matplotlib")
    from pymchelper.writers.plots import ImageWriter

    page = fromfile(path).pages[0]
    fig = ImageWriter("out", argparse.Namespace(colormap='gnuplot2', log=[])).get_page_figure(page)
    pixels = np.asarray(fig.axes[0].images[0].get_array())

    np.testing.assert_array_equal(pixels, np.squeeze(page.data).T)


@pytest.mark.parametrize("converter", ["txt", "image"])
def test_output_without_directory(converter: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A multi-page output name without a directory part goes to the working directory"""
    if converter == "image":
        pytest.importorskip("matplotlib")
    monkeypatch.chdir(tmp_path)
    estimator = fromfile(mesh_2d_files[0])
    tofile(estimator, "out", converter, argparse.Namespace(colormap='gnuplot2', log=[]))

    assert len(list(tmp_path.glob("out_p*"))) == len(estimator.pages)


def test_plotdata_0dim_pages(tmp_path: Path):
    """Each 0-dim page goes to its own file"""
    estimator = fromfile(res_dir / "averaging" / "normalisation-5_aggregation-mean_0001.bdo")
    tofile(estimator, str(tmp_path / "out"), "plotdata", None)

    for i, page in enumerate(estimator.pages):
        assert np.loadtxt(tmp_path / f"out_p{i + 1}.dat") == pytest.approx(page.data_raw.item(), rel=1e-5)


@pytest.mark.parametrize("value", [
    0.0, -0.0, 1.0, -1.0, 9.99999995, 0.12345675, 1.5e-5, -123.456, 1e-99, 1e-120, 1e120, 5e-324,
    float('nan'),
    float('inf'), -float('inf')
])
def test_format_e_fast(value: float):
    """Fast path gives the same string as the Fortran formatter"""
    for w, d in ((14, 7), (23, 16)):
        assert _format_e_fast(w, d, value) == format_e(w, d, value)
