"""Regression tests for differential axis binning detection in the BDO 2019 reader.

See https://github.com/DataMedSci/pymchelper/issues/868 : log-scaled differential
axes (Diff1/Diff2 with the ``log`` keyword in detect.dat) were always reported as
linear because the reader ignored the ``page_diff_flag`` tag written by SHIELD-HIT12A.
"""

from pathlib import Path

import numpy as np
import pytest

from pymchelper.axis import MeshAxis
from pymchelper.input_output import fromfile
from pymchelper.readers.shieldhit.reader_bdo2019 import _diff_axis_binning

res_dir = Path("tests") / "res" / "shieldhit" / "diff_scoring"


@pytest.mark.smoke
def test_log_diff_axis_is_detected_as_logarithmic():
    """A Diff1 axis configured with the `log` keyword should have logarithmic binning."""
    estimator = fromfile(res_dir / "fluence_elog.bdo")
    diff_axis = estimator.pages[0].diff_axis1

    assert diff_axis.binning == MeshAxis.BinningType.logarithmic
    assert diff_axis.n == 10
    assert diff_axis.min_val == pytest.approx(0.01)
    assert diff_axis.max_val == pytest.approx(100.0)


@pytest.mark.smoke
def test_lin_diff_axis_is_detected_as_linear():
    """A Diff1 axis configured with the `lin` keyword should have linear binning."""
    estimator = fromfile(res_dir / "fluence_elin.bdo")
    diff_axis = estimator.pages[0].diff_axis1

    assert diff_axis.binning == MeshAxis.BinningType.linear
    assert diff_axis.n == 10
    assert diff_axis.min_val == pytest.approx(0.01)
    assert diff_axis.max_val == pytest.approx(100.0)


@pytest.mark.smoke
def test_2d_log_diff_axes_are_detected_as_logarithmic():
    """With 2-D differential scoring (Diff1 + Diff2), both log-configured axes are logarithmic."""
    estimator = fromfile(res_dir / "fluence_2d_log.bdo")
    page = estimator.pages[0]

    assert page.diff_axis1.binning == MeshAxis.BinningType.logarithmic
    assert page.diff_axis2.binning == MeshAxis.BinningType.logarithmic
    assert page.diff_axis2.n == 5
    assert page.diff_axis2.min_val == pytest.approx(0.01)
    assert page.diff_axis2.max_val == pytest.approx(3.14)


@pytest.mark.smoke
def test_2d_lin_diff_axes_are_detected_as_linear():
    """With 2-D differential scoring (Diff1 + Diff2), both lin-configured axes are linear."""
    estimator = fromfile(res_dir / "fluence_2d_lin.bdo")
    page = estimator.pages[0]

    assert page.diff_axis1.binning == MeshAxis.BinningType.linear
    assert page.diff_axis2.binning == MeshAxis.BinningType.linear
    assert page.diff_axis2.n == 5
    assert page.diff_axis2.min_val == pytest.approx(0.0)
    assert page.diff_axis2.max_val == pytest.approx(3.14)


@pytest.mark.smoke
def test_diff_axis_binning_missing_flag_defaults_to_linear():
    """No page_diff_flag tag at all (e.g. an old BDO file) should default to linear."""
    assert _diff_axis_binning(None, 0) == MeshAxis.BinningType.linear


@pytest.mark.smoke
def test_diff_axis_binning_handles_scalar_flag():
    """A single differential axis may be stored as a bare scalar rather than an array."""
    assert _diff_axis_binning(np.int32(-1), 0) == MeshAxis.BinningType.logarithmic
    assert _diff_axis_binning(np.int32(1), 0) == MeshAxis.BinningType.linear


@pytest.mark.smoke
def test_diff_axis_binning_out_of_range_index_defaults_to_linear():
    """Asking for the second axis when only one flag was written should default to linear."""
    assert _diff_axis_binning(np.array([-1]), 1) == MeshAxis.BinningType.linear


@pytest.mark.smoke
def test_diff_axis_binning_reads_correct_element_of_two_element_array():
    """Each axis picks its own element out of a 2-element page_diff_flag array."""
    flags = np.array([-1, 1])
    assert _diff_axis_binning(flags, 0) == MeshAxis.BinningType.logarithmic
    assert _diff_axis_binning(flags, 1) == MeshAxis.BinningType.linear
