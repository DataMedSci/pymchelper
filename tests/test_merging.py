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
dose_files = sorted(str(path) for path in averaging_dir.glob("normalisation-5_aggregation-mean_*.bdo"))


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
        assert default[name].item() == without_nan_skipping[name].item()


def test_skip_nan_weighted_mean_and_variance():
    """NaN values are left out bin by bin, the rest is weighted as usual"""
    rng = np.random.default_rng(0)
    files_count = 6
    bins_count = 50
    values = rng.normal(5.0, 1.0, size=(files_count, bins_count))
    missing = rng.random(values.shape) < 0.3
    values[missing] = np.nan
    empty_bin = 0
    values[:, empty_bin] = np.nan
    file_weights = np.array([10.0, 20.0, 30.0, 10.0, 50.0, 5.0])

    aggregator = WeightedStatsAggregator(skip_nan=True)
    for file_values, file_weight in zip(values, file_weights):
        aggregator.update(file_values, file_weight)

    # reference: the usual weighted formulas, computed for each bin from its non-NaN values only
    expected_mean = np.full(bins_count, np.nan)
    expected_variance_sample = np.full(bins_count, np.nan)
    for bin_index in range(bins_count):
        bin_values = values[:, bin_index]
        present = ~np.isnan(bin_values)
        if not present.any():
            continue
        present_values = bin_values[present]
        present_weights = file_weights[present]
        total_weight = present_weights.sum()
        mean = np.sum(present_weights * present_values) / total_weight
        squared_deviations = np.sum(present_weights * (present_values - mean)**2)
        bias_corrected_weight = total_weight - np.sum(present_weights**2) / total_weight
        expected_mean[bin_index] = mean
        expected_variance_sample[bin_index] = squared_deviations / bias_corrected_weight

    assert np.isnan(aggregator.mean[empty_bin])
    assert np.isnan(aggregator.stderr[empty_bin])
    np.testing.assert_allclose(aggregator.mean, expected_mean, rtol=1e-12)
    np.testing.assert_allclose(aggregator.variance_sample, expected_variance_sample, rtol=1e-9)


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
    files = []
    for _ in range(5):
        files.extend(dose_files)
    io.fromfilelist(files)

    still_alive = [reference for reference in references[1:] if reference() is not None]
    assert len(still_alive) == 0


@pytest.mark.parametrize("nan", [True, False])
def test_page_nan_in_every_file_stays_nan(monkeypatch: pytest.MonkeyPatch, nan: bool):
    """A page with no value in any file (e.g. LET where nothing deposited dose) is NaN, with NaN error"""
    original_fromfile = io.fromfile

    def fromfile_without_values(filename):
        estimator = original_fromfile(filename)
        for page in estimator.pages:
            page.data_raw = np.full(page.data_raw.shape, np.nan)
        return estimator

    monkeypatch.setattr(io, "fromfile", fromfile_without_values)
    estimators = io.frompattern(str(averaging_dir / "normalisation-3_aggregation-mean_*.bdo"), nan=nan)

    for page in estimators[0].pages:
        assert np.isnan(page.data_raw).all()
        assert np.isnan(page.error_raw).all()


@pytest.mark.parametrize("nan", [True, False])
def test_files_without_primaries_give_nan(monkeypatch: pytest.MonkeyPatch, nan: bool):
    """Files with 0 primaries carry no weight, so the weighted mean and its error are NaN"""
    original_fromfile = io.fromfile

    def fromfile_without_primaries(filename):
        estimator = original_fromfile(filename)
        estimator.number_of_primaries = 0
        return estimator

    monkeypatch.setattr(io, "fromfile", fromfile_without_primaries)
    merged = io.fromfilelist(dose_files, nan=nan)

    for page in merged.pages:
        assert np.isnan(page.data_raw).all()
        assert np.isnan(page.error_raw).all()
