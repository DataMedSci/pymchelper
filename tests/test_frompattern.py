import pytest
from pymchelper.input_output import frompattern


@pytest.fixture
def shieldhit_pattern() -> str:
    """Fixture for SHIELD-HIT file pattern"""
    return "tests/res/shieldhit/generated/many/msh/aen_*.bdo"


def test_estimators_are_sorted_by_names(shieldhit_pattern: str) -> None:
    """Test if frompattern returns estimators sorted by name"""
    averaged_estimators = frompattern(pattern=shieldhit_pattern)
    estimator_names = [estimator.file_corename for estimator in averaged_estimators]
    assert estimator_names == sorted(estimator_names), "Estimators are not sorted by file names"
