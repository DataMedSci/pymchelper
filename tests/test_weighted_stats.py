import pytest
import numpy as np
from numpy.typing import NDArray
from pymchelper.averaging import WeightedStatsAggregator


def test_initial_state() -> None:
    ws = WeightedStatsAggregator()
    # check if ws.mean is nan
    assert np.isnan(ws.mean)
    assert ws.total_weight == 0


def test_single_update() -> None:
    ws = WeightedStatsAggregator()
    ws.update(value=10, weight=2)
    assert ws.mean == 10
    assert ws.total_weight == 2


def test_multiple_updates() -> None:
    ws = WeightedStatsAggregator()
    updates = [(10, 2), (20, 3), (30, 5)]
    total_weight = sum(weight for _, weight in updates)
    weighted_sum = sum(value * weight for value, weight in updates)
    expected_mean = weighted_sum / total_weight

    for value, weight in updates:
        ws.update(value, weight)

    assert ws.total_weight == total_weight
    assert pytest.approx(ws.mean, 0.001) == expected_mean


def test_zero_weight() -> None:
    ws = WeightedStatsAggregator()
    with pytest.raises(Exception):
        ws.update(value=10, weight=0)


def test_negative_weight() -> None:
    ws = WeightedStatsAggregator()
    with pytest.raises(Exception):
        ws.update(value=10, weight=-1)


def test_update_with_1d_array() -> None:
    ws = WeightedStatsAggregator()
    values = np.array([10, 20, 30])
    weights = np.array([2, 3, 5])
    total_weight = weights.sum()
    weighted_sum = np.dot(values, weights)
    expected_mean = weighted_sum / total_weight

    for value, weight in zip(values, weights):
        ws.update(value, weight)

    assert ws.total_weight == total_weight
    assert pytest.approx(ws.mean, 0.001) == expected_mean


def test_update_with_flattened_array() -> None:
    ws = WeightedStatsAggregator()
    values = np.array([[10, 20], [30, 40]]).flatten()
    weights = np.array([[2, 3], [4, 1]]).flatten()
    total_weight = weights.sum()
    weighted_sum = np.dot(values, weights)
    expected_mean = weighted_sum / total_weight

    for value, weight in zip(values, weights):
        ws.update(value, weight)

    assert ws.total_weight == total_weight
    assert pytest.approx(ws.mean, 0.001) == expected_mean


def compute_expected_variance(values: NDArray[np.floating],
                              weights: NDArray[np.floating],
                              total_weight: float,
                              is_sample: bool = False) -> float:
    """Utility function to compute the expected variance."""
    weighted_mean = np.average(values, weights=weights)
    variance = np.sum(weights * (values - weighted_mean)**2)
    if is_sample:
        variance /= (total_weight - (np.sum(weights**2) / total_weight))
    else:
        variance /= total_weight
    return variance


def test_variance_population_single_update() -> None:
    ws = WeightedStatsAggregator()
    ws.update(value=10, weight=2)
    # Variance should be 0 for a single value
    assert ws.variance_population == 0


def test_variance_population_multiple_updates() -> None:
    ws = WeightedStatsAggregator()
    values = np.array([10, 20, 30])
    weights = np.array([2, 3, 5])
    total_weight = weights.sum()

    for value, weight in zip(values, weights):
        ws.update(value, weight)

    expected_variance = compute_expected_variance(values, weights, total_weight)
    assert pytest.approx(ws.variance_population, 0.001) == expected_variance


def test_variance_sample_multiple_updates() -> None:
    ws = WeightedStatsAggregator()
    values = np.array([10, 20, 30])
    weights = np.array([2, 3, 5])
    total_weight = weights.sum()

    for value, weight in zip(values, weights):
        ws.update(value, weight)

    expected_variance = compute_expected_variance(values, weights, total_weight, is_sample=True)
    assert pytest.approx(ws.variance_sample, 0.001) == expected_variance


def test_variance_with_1d_array() -> None:
    ws = WeightedStatsAggregator()
    values = np.array([10, 20, 30])
    weights = np.array([2, 3, 5])
    total_weight = weights.sum()

    for value, weight in zip(values, weights):
        ws.update(value, weight)

    expected_variance_population = compute_expected_variance(values, weights, total_weight)
    assert pytest.approx(ws.variance_population, 0.001) == expected_variance_population

    expected_variance_sample = compute_expected_variance(values, weights, total_weight, is_sample=True)
    assert pytest.approx(ws.variance_sample, 0.001) == expected_variance_sample


def test_variance_with_array_updates() -> None:
    """Each update is a whole array, as when aggregating pages of several files"""
    ws = WeightedStatsAggregator()
    pages = np.array([[0.0, 1.0, 10.0], [2.0, 4.0, 10.0], [7.0, 2.0, 40.0], [3.0, 8.0, 20.0]])
    weights = np.array([1.0, 1.0, 1.0, 3.0])

    for page, weight in zip(pages, weights):
        ws.update(page, weight)

    for i in range(pages.shape[1]):
        expected_population = compute_expected_variance(pages[:, i], weights, weights.sum())
        expected_sample = compute_expected_variance(pages[:, i], weights, weights.sum(), is_sample=True)
        assert ws.mean[i] == pytest.approx(np.average(pages[:, i], weights=weights))
        assert ws.variance_population[i] == pytest.approx(expected_population)
        assert ws.variance_sample[i] == pytest.approx(expected_sample)


def test_float32_arrays_with_large_offset() -> None:
    """Accumulates in float64 and keeps the variance accurate when mean / sd is large"""
    rng = np.random.default_rng(0)
    pages = (1e6 + rng.standard_normal((100, 5))).astype(np.float32)
    ws = WeightedStatsAggregator()

    for page in pages:
        ws.update(page)

    reference = pages.astype(np.float64)
    assert np.asarray(ws.mean).dtype == np.float64
    np.testing.assert_allclose(ws.mean, reference.mean(axis=0), rtol=1e-12)
    np.testing.assert_allclose(ws.variance_sample, reference.var(axis=0, ddof=1), rtol=1e-9)


def test_zero_weight_after_first_update() -> None:
    """A zero-weight update after the first one changes nothing"""
    ws = WeightedStatsAggregator()
    ws.update(np.array([1.0, 2.0]), 2)
    ws.update(np.array([5.0, 9.0]), 0)

    np.testing.assert_array_equal(ws.mean, [1.0, 2.0])
    assert ws.total_weight == 2
