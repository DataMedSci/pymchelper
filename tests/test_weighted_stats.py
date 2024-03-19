import pytest
from pymchelper.averaging import WeightedStats  # Make sure to import your class correctly


def test_initial_state():
    ws = WeightedStats()
    assert ws.mean == 0
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
    with pytest.raises(Exception):  # Replace Exception with the specific exception you expect
        ws.update(value=10, weight=0)


def test_negative_weight():
    ws = WeightedStats()
    with pytest.raises(Exception):  # Replace Exception with the specific exception you expect
        ws.update(value=10, weight=-1)
