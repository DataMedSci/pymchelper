import pytest
import numpy as np
from pymchelper.averaging import WeightedStats


def test_initial_state():
    ws = WeightedStats()
    # check if ws.mean is nan
    assert np.isnan(ws.mean)
    assert ws.total_weight == 0


def test_single_update():
    ws = WeightedStats()
    ws.update(value=10, weight=2)
    assert ws.mean == 10
    assert ws.total_weight == 2


def test_multiple_updates():
    ws = WeightedStats()
    updates = [(10, 2), (20, 3), (30, 5)]
    total_weight = sum(weight for _, weight in updates)
    weighted_sum = sum(value * weight for value, weight in updates)
    expected_mean = weighted_sum / total_weight

    for value, weight in updates:
        ws.update(value, weight)

    assert ws.total_weight == total_weight
    assert pytest.approx(ws.mean, 0.001) == expected_mean


def test_zero_weight():
    ws = WeightedStats()
    with pytest.raises(Exception):
        ws.update(value=10, weight=0)


def test_negative_weight():
    ws = WeightedStats()
    with pytest.raises(Exception):
        ws.update(value=10, weight=-1)


def test_update_with_1d_array():
    ws = WeightedStats()
    values = np.array([10, 20, 30])
    weights = np.array([2, 3, 5])
    total_weight = weights.sum()
    weighted_sum = np.dot(values, weights)
    expected_mean = weighted_sum / total_weight

    for value, weight in zip(values, weights):
        ws.update(value, weight)

    assert ws.total_weight == total_weight
    assert pytest.approx(ws.mean, 0.001) == expected_mean


def test_update_with_flattened_array():
    ws = WeightedStats()
    values = np.array([[10, 20], [30, 40]]).flatten()
    weights = np.array([[2, 3], [4, 1]]).flatten()
    total_weight = weights.sum()
    weighted_sum = np.dot(values, weights)
    expected_mean = weighted_sum / total_weight

    for value, weight in zip(values, weights):
        ws.update(value, weight)

    assert ws.total_weight == total_weight
    assert pytest.approx(ws.mean, 0.001) == expected_mean


def compute_expected_variance(values, weights, total_weight, is_sample=False):
    """Utility function to compute the expected variance."""
    weighted_mean = np.average(values, weights=weights)
    variance = np.sum(weights * (values - weighted_mean)**2)
    if is_sample:
        variance /= (total_weight - 1)
    else:
        variance /= total_weight
    return variance


def test_variance_population_single_update():
    ws = WeightedStats()
    ws.update(value=10, weight=2)
    # Variance should be 0 for a single value
    assert ws.variance_population() == 0


def test_variance_population_multiple_updates():
    ws = WeightedStats()
    values = np.array([10, 20, 30])
    weights = np.array([2, 3, 5])
    total_weight = weights.sum()

    for value, weight in zip(values, weights):
        ws.update(value, weight)

    expected_variance = compute_expected_variance(values, weights, total_weight)
    assert pytest.approx(ws.variance_population(), 0.001) == expected_variance


def test_variance_sample_multiple_updates():
    ws = WeightedStats()
    values = np.array([10, 20, 30])
    weights = np.array([2, 3, 5])
    total_weight = weights.sum()

    for value, weight in zip(values, weights):
        ws.update(value, weight)

    # Sample variance calculation should only be used when there are at least two samples
    if total_weight > 1:
        expected_variance = compute_expected_variance(values, weights, total_weight, is_sample=True)
        assert pytest.approx(ws.variance_sample(), 0.001) == expected_variance
    else:
        with pytest.raises(ZeroDivisionError):
            _ = ws.variance_sample()


def test_variance_with_1d_array():
    ws = WeightedStats()
    values = np.array([10, 20, 30])
    weights = np.array([2, 3, 5])
    total_weight = weights.sum()

    for value, weight in zip(values, weights):
        ws.update(value, weight)

    expected_variance_population = compute_expected_variance(values, weights, total_weight)
    assert pytest.approx(ws.variance_population(), 0.001) == expected_variance_population

    if total_weight > 1:
        expected_variance_sample = compute_expected_variance(values, weights, total_weight, is_sample=True)
        assert pytest.approx(ws.variance_sample(), 0.001) == expected_variance_sample
