"""Writers put every value on its own bin, whatever the memory order of the input format"""
import argparse
import json
from pathlib import Path
from typing import List

import numpy as np
import pytest

from pymchelper.estimator import Estimator
from pymchelper.input_output import fromfile, tofile
from pymchelper.readers.shieldhit.reader_bin2010 import SHReaderBin2010
from pymchelper.writers.fortranformatter import format_e
from pymchelper.writers.shieldhit import _format_e_fast
from pymchelper.writers.trip98ddd import TRiP98DDDWriter

res_dir = Path(__file__).resolve().parent / "res" / "shieldhit"
mesh_2d_files = [
    str(res_dir / "v1.0.0" / "ex_yzmsh.bdo"),  # BDO2019, file stores bins with x fastest
    str(res_dir / "single" / "ex_yzmsh.bdo"),  # bin2010, file stores bins with z fastest
]
cylinder_rz_bin2010_file = str(res_dir / "generated" / "many" / "cyl" / "aen_xz_al0001.bdo")


def nearest_bin_indices(bin_centres: np.ndarray, coordinates: np.ndarray) -> List[int]:
    """For each coordinate return the index of the closest bin centre"""
    indices = []
    for coordinate in coordinates:
        distances = np.abs(bin_centres - coordinate)
        indices.append(int(np.argmin(distances)))
    return indices


def test_bin2010_bins_on_their_place():
    """bin2010 files store the bins with the last axis fastest, page.data has each of them on its (x, y, z) place"""
    page = fromfile(cylinder_rz_bin2010_file).pages[0]

    file_estimator = Estimator()
    reader = SHReaderBin2010(cylinder_rz_bin2010_file)
    reader.read_header(file_estimator)
    reader.read_payload(file_estimator)
    values_in_file_order = file_estimator.pages[0].data_raw

    expected_data = values_in_file_order.reshape(page.data.shape, order='C')
    np.testing.assert_array_equal(page.data, expected_data)


@pytest.mark.parametrize("path", mesh_2d_files, ids=["bdo2019", "bin2010"])
def test_json_values(path: str, tmp_path: Path):
    """JSON values walk the bins with the first axis fastest"""
    estimator = fromfile(path)
    tofile(estimator, str(tmp_path / "out"), "json", None)
    output = json.loads((tmp_path / "out.json").read_text())
    page_dict = output["pages"][0]
    first_axis_size = len(page_dict["axis_dim1"]["values"])
    second_axis_size = len(page_dict["axis_dim2"]["values"])

    values_first_axis_fastest = np.array(page_dict["data"]["values"])
    values_grid = values_first_axis_fastest.reshape((second_axis_size, first_axis_size))
    values = values_grid.T
    np.testing.assert_array_equal(values, np.squeeze(estimator.pages[0].data))
    assert "data_order" not in output["metadata"]


@pytest.mark.parametrize("path", mesh_2d_files, ids=["bdo2019", "bin2010"])
def test_txt_rows(path: str, tmp_path: Path):
    """Each txt row holds the value of the bin at its coordinates"""
    estimator = fromfile(path)
    estimator.pages = estimator.pages[:1]
    page = estimator.pages[0]
    tofile(estimator, str(tmp_path / "out"), "txt", None)
    rows = np.loadtxt(tmp_path / "out.txt")

    x_indices = nearest_bin_indices(page.axis(0).data, rows[:, 0])
    y_indices = nearest_bin_indices(page.axis(1).data, rows[:, 1])
    z_indices = nearest_bin_indices(page.axis(2).data, rows[:, 2])
    expected_values = page.data[x_indices, y_indices, z_indices, 0, 0]
    np.testing.assert_allclose(rows[:, 3], expected_values, rtol=1e-15)


def test_txt_differential_page(tmp_path: Path):
    """txt has no columns for differential axes, such a page raises an error instead of being cut short"""
    estimator = fromfile(str(res_dir / "diff_scoring" / "fluence_2d_lin.bdo"))

    with pytest.raises(ValueError, match="differential axes"):
        tofile(estimator, str(tmp_path / "out"), "txt", None)


@pytest.mark.parametrize("path", mesh_2d_files, ids=["bdo2019", "bin2010"])
def test_plotdata_rows(path: str, tmp_path: Path):
    """Each plotdata row holds the value of the bin at its coordinates"""
    estimator = fromfile(path)
    estimator.pages = estimator.pages[:1]
    page = estimator.pages[0]
    tofile(estimator, str(tmp_path / "out"), "plotdata", None)
    rows = np.loadtxt(tmp_path / "out.dat")

    # the x axis has a single bin, so the columns are y, z and value
    y_indices = nearest_bin_indices(page.axis(1).data, rows[:, 0])
    z_indices = nearest_bin_indices(page.axis(2).data, rows[:, 1])
    expected_values = page.data[0, y_indices, z_indices, 0, 0]
    np.testing.assert_allclose(rows[:, 2], expected_values, rtol=1e-5)


def test_trip98ddd_profile():
    """The depth-dose profile has depth along rows and radius along columns"""
    estimator = fromfile(cylinder_rz_bin2010_file)
    page = estimator.pages[0]
    page.error_raw = np.zeros_like(page.data_raw)  # a single file has no errors, which this writer requires

    profile = TRiP98DDDWriter._extract_data(estimator, page)

    radius_depth_values = page.data[:, 0, :, 0, 0]
    np.testing.assert_array_equal(profile.dose_MeV_g_2d, radius_depth_values.T)


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
    for width, digits in ((14, 7), (23, 16)):
        assert _format_e_fast(width, digits, value) == format_e(width, digits, value)
