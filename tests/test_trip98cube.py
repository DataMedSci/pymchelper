"""Tests for tripcube converter"""
from pathlib import Path

import numpy as np
import pytest

from pymchelper.axis import MeshAxis
from pymchelper.estimator import Estimator
from pymchelper.input_output import fromfile, tofile
from pymchelper.page import Page
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

shieldhit_dir = Path(__file__).resolve().parent / "res" / "shieldhit"


def mesh_axis(n: int, min_val: float, max_val: float) -> MeshAxis:
    """Linear mesh axis in cm"""
    return MeshAxis(n=n, min_val=min_val, max_val=max_val, name="", unit="cm", binning=MeshAxis.BinningType.linear)


def mesh_estimator(page_types: list) -> Estimator:
    """Estimator on a 2 x 3 x 4 mesh with 2 mm X and Y bins, 5 mm Z bins, X from -2 mm, Y from -4 mm, Z from 10 mm.

    Each page gets distinct positive values, so a wrong axis order or offset shows up in the comparison.
    """
    estimator = Estimator()
    estimator.geotyp = SHGeoType.msh
    for page_type in page_types:
        page = Page()
        page.dettyp = page_type
        page.x = mesh_axis(n=2, min_val=-0.2, max_val=0.2)
        page.y = mesh_axis(n=3, min_val=-0.4, max_val=0.2)
        page.z = mesh_axis(n=4, min_val=1.0, max_val=3.0)
        page.data_raw = np.arange(1.0, 25.0) * 0.37
        estimator.add_page(page)
    return estimator


def read_cube(cube_class, header_path: Path):
    """Read a TRiP98 cube with PyTRiP"""
    cube = cube_class()
    cube.read(str(header_path))
    return cube


def check_geometry(cube):
    """Cube geometry in mm matches the mesh of `mesh_estimator`"""
    assert cube.cube.shape == (4, 3, 2)
    assert cube.pixel_size == pytest.approx(2.0)
    assert cube.slice_distance == pytest.approx(5.0)
    assert cube.xoffset == pytest.approx(-2.0)
    assert cube.yoffset == pytest.approx(-4.0)
    assert cube.slice_pos == pytest.approx([12.5, 17.5, 22.5, 27.5])


def test_dose_cube(tmp_path: Path):
    """DOSE page is written as (z, y, x) cube rounded to integers and scaled to 1200 at maximum"""
    pytest.importorskip("pytrip")
    from pytrip import dos

    estimator = mesh_estimator([SHDetType.dose])
    page = estimator.pages[0]

    tofile(estimator, str(tmp_path / "dose"), "tripcube", None)

    cube = read_cube(dos.DosCube, tmp_path / "dose.hed")
    check_geometry(cube)
    page_data_zyx = page.data[:, :, :, 0, 0].transpose()
    expected = np.rint(page_data_zyx / page_data_zyx.max() * 1200.0)
    np.testing.assert_array_equal(cube.cube, expected)


def test_dose_cube_with_trip_normalisation(tmp_path: Path):
    """DOSE page is scaled with planned dose and number of primaries when the file carries them"""
    pytest.importorskip("pytrip")
    from pytrip import dos

    estimator = mesh_estimator([SHDetType.dose])
    page = estimator.pages[0]
    estimator.tripdose = 2.0
    estimator.tripntot = 10**9

    tofile(estimator, str(tmp_path / "dose"), "tripcube", None)

    cube = read_cube(dos.DosCube, tmp_path / "dose.hed")
    page_data_zyx = page.data[:, :, :, 0, 0].transpose()
    expected = np.rint(page_data_zyx * estimator.tripntot * 1.602e-10 / estimator.tripdose * 1000.0)
    np.testing.assert_array_equal(cube.cube, expected)


def test_let_cube(tmp_path: Path):
    """TLET page is written as (z, y, x) cube in keV/um, page data stays in MeV/cm"""
    pytest.importorskip("pytrip")
    from pytrip import let

    estimator = mesh_estimator([SHDetType.tlet])
    page = estimator.pages[0]
    page_data_before = page.data_raw.copy()

    tofile(estimator, str(tmp_path / "let"), "tripcube", None)

    cube = read_cube(let.LETCube, tmp_path / "let.hed")
    check_geometry(cube)
    page_data_zyx = page.data[:, :, :, 0, 0].transpose()
    np.testing.assert_allclose(cube.cube, page_data_zyx * 0.1, rtol=1e-6)
    np.testing.assert_array_equal(page.data_raw, page_data_before)


def test_each_page_to_own_cube(tmp_path: Path):
    """Dose and LET pages go to numbered cubes, pages of other quantities are skipped"""
    pytest.importorskip("pytrip")

    estimator = mesh_estimator([SHDetType.dose, SHDetType.fluence, SHDetType.dlet])

    tofile(estimator, str(tmp_path / "cube"), "tripcube", None)

    written_files = sorted(path.name for path in tmp_path.iterdir())
    assert written_files == ["cube_p1.dos", "cube_p1.hed", "cube_p3.dos", "cube_p3.hed"]


def differential_estimator() -> Estimator:
    """Single DOSE page with an energy differential axis"""
    estimator = mesh_estimator([SHDetType.dose])
    estimator.pages[0].diff_axis1 = mesh_axis(n=3, min_val=0.0, max_val=3.0)
    estimator.pages[0].data_raw = np.ones(72)
    return estimator


def unequal_pixels_estimator() -> Estimator:
    """YZ mesh file with 1 X bin of 10 cm and 100 Y bins of 1 mm, its first page is DOSE"""
    return fromfile(str(shieldhit_dir / "v1.0.0" / "ex_yzmsh.bdo"))


def half_pixel_offset_estimator() -> Estimator:
    """DOSE page on a mesh starting half a pixel off the TRiP98 grid"""
    estimator = mesh_estimator([SHDetType.dose])
    estimator.pages[0].x = mesh_axis(n=2, min_val=-0.3, max_val=0.1)
    return estimator


def cylinder_estimator() -> Estimator:
    """DOSE page on a cylindrical mesh"""
    estimator = mesh_estimator([SHDetType.dose])
    estimator.geotyp = SHGeoType.cyl
    return estimator


def phase_space_estimator() -> Estimator:
    """Single page phase space file"""
    return fromfile(str(shieldhit_dir / "averaging" / "normalisation-4_aggregation-concat_0001.bdo"))


@pytest.mark.parametrize("make_estimator, message", [
    (differential_estimator, "differential axes"),
    (unequal_pixels_estimator, "one pixel size for X and Y"),
    (half_pixel_offset_estimator, "X offset as a whole number of pixels"),
    (cylinder_estimator, "cartesian mesh"),
    (phase_space_estimator, "only dose and LET pages"),
])
def test_unsupported_data_raises(make_estimator, message: str, tmp_path: Path):
    """Data that does not fit into a TRiP98 cube raises an error and writes nothing"""
    pytest.importorskip("pytrip")

    estimator = make_estimator()

    with pytest.raises(ValueError, match=message):
        tofile(estimator, str(tmp_path / "cube"), "tripcube", None)
    assert list(tmp_path.iterdir()) == []
