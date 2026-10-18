"""Merging output files: one merge path for every page type, with and without skipping NaN values"""
import shutil
import weakref
from pathlib import Path

import numpy as np
import pytest

import pymchelper.input_output as io
from pymchelper.averaging import ConcatenatingAggregator, SumAggregator, WeightedStatsAggregator
from pymchelper.readers.fluka import FlukaReader

averaging_dir = Path(__file__).resolve().parent / "res" / "shieldhit" / "averaging"


def merged_pages(nan: bool) -> dict:
    """Merge every group of files in averaging_dir, return {page name: data}"""
    result = {}
    for estimator in io.frompattern(str(averaging_dir / "*.bdo"), nan=nan):
        for page in estimator.pages:
            result[page.name] = page.data_raw
    return result


def test_frompattern_default_follows_page_rules():
    """The default of frompattern (nan=True) sums, averages with weights and concatenates like nan=False"""
    default = merged_pages(nan=True)
    without_nan_skipping = merged_pages(nan=False)

    assert default["COUNT"].item() == 19128
    assert default["MCPL"].size == 11856
    for name in ("DOSE", "FLUENCE", "DLET", "TLET"):
        assert default[name].item() == pytest.approx(without_nan_skipping[name].item(), rel=1e-14)


def test_skip_nan_weighted_mean_and_variance():
    """NaN values are left out bin by bin, the rest is weighted as usual"""
    rng = np.random.default_rng(0)
    values = rng.normal(5.0, 1.0, size=(6, 50))
    values[rng.random(values.shape) < 0.3] = np.nan
    values[:, 0] = np.nan  # a bin with no value at all
    weights = np.array([10.0, 20.0, 30.0, 10.0, 50.0, 5.0])

    aggregator = WeightedStatsAggregator(skip_nan=True)
    for page, weight in zip(values, weights):
        aggregator.update(page, weight)

    # reference: the usual weighted formulas, with NaN entries masked out in each bin
    masked = np.ma.masked_invalid(values)
    bin_weights = np.ma.masked_array(np.broadcast_to(weights[:, None], values.shape), mask=masked.mask)
    total_weight = bin_weights.sum(axis=0)
    mean = (bin_weights * masked).sum(axis=0) / total_weight
    variance_sample = (bin_weights * (masked - mean)**2).sum(axis=0) / (total_weight -
                                                                        (bin_weights**2).sum(axis=0) / total_weight)

    assert np.isnan(aggregator.mean[0])
    np.testing.assert_allclose(aggregator.mean[1:], mean[1:].filled(np.nan), rtol=1e-12)
    np.testing.assert_allclose(aggregator.variance_sample[1:], variance_sample[1:].filled(np.nan), rtol=1e-9)


def test_skip_nan_sum():
    """NaN values count as 0, a bin with only NaN values stays NaN"""
    aggregator = SumAggregator(skip_nan=True)
    aggregator.update(np.array([1.0, np.nan, np.nan]))
    aggregator.update(np.array([2.0, 3.0, np.nan]))

    np.testing.assert_array_equal(aggregator.data, [3.0, 3.0, np.nan])


def test_concatenating_aggregator():
    """Concatenation gives the arrays one after another"""
    parts = [np.arange(3.0), np.arange(5.0), np.arange(2.0)]
    aggregator = ConcatenatingAggregator()
    for part in parts:
        aggregator.update(part)

    np.testing.assert_array_equal(aggregator.data, np.concatenate(parts))


def test_different_scorers_are_not_merged():
    """Files with different pages raise an error naming them"""
    files = [
        str(averaging_dir / "normalisation-5_aggregation-mean_0001.bdo"),
        str(averaging_dir / "normalisation-3_aggregation-mean_0001.bdo")
    ]
    with pytest.raises(ValueError, match="normalisation-3_aggregation-mean_0001.bdo"):
        io.fromfilelist(files)


def test_fort_in_directory_name(tmp_path: Path):
    """A directory with _fort in its name doesn't make SHIELD-HIT12A files look like FLUKA files"""
    directory = tmp_path / "sim_fortran"
    directory.mkdir()
    for path in averaging_dir.glob("normalisation-[35]_aggregation-mean_000[12].bdo"):
        shutil.copy(path, directory)

    estimators = io.frompattern(str(directory / "*.bdo"), nan=False)

    assert sorted(estimator.file_corename for estimator in estimators) == [
        "normalisation-3_aggregation-mean", "normalisation-5_aggregation-mean"
    ]
    assert FlukaReader(str(directory / "x.bdo")).corename is None
    assert FlukaReader(str(directory / "run001_fort.21")).corename == "21"


def test_estimators_freed_while_merging(monkeypatch: pytest.MonkeyPatch):
    """Each file read for merging is freed right after it is used"""
    references = []
    original_fromfile = io.fromfile

    def tracked_fromfile(filename):
        estimator = original_fromfile(filename)
        references.append(weakref.ref(estimator))
        return estimator

    monkeypatch.setattr(io, "fromfile", tracked_fromfile)
    files = sorted(str(path) for path in averaging_dir.glob("normalisation-5_aggregation-mean_*.bdo")) * 5
    io.fromfilelist(files)

    still_alive = [reference for reference in references[1:] if reference() is not None]
    assert len(still_alive) == 0
