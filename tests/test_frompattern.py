from glob import glob

import pytest
from pymchelper.input_output import convertfrompattern, frompattern


@pytest.fixture
def shieldhit_pattern() -> str:
    """Fixture for SHIELD-HIT file pattern"""
    return "tests/res/shieldhit/generated/many/msh/aen_*.bdo"


def test_estimators_are_sorted_by_names(shieldhit_pattern: str) -> None:
    """Test if frompattern returns estimators sorted by name"""
    averaged_estimators = frompattern(pattern=shieldhit_pattern)
    estimator_names = [estimator.file_corename for estimator in averaged_estimators]
    assert estimator_names == sorted(estimator_names), "Estimators are not sorted by file names"


def test_file_list_gives_same_estimators_as_pattern(shieldhit_pattern: str) -> None:
    """Test if frompattern accepts a list of files, as Runner.get_data passes one"""
    from_pattern = frompattern(pattern=shieldhit_pattern)
    from_list = frompattern(pattern=sorted(glob(shieldhit_pattern)))
    assert [e.file_corename for e in from_list] == [e.file_corename for e in from_pattern]


def test_convertfrompattern_without_matching_files(tmp_path) -> None:
    """Test if convertfrompattern reports an error status instead of raising when no file matches"""
    status = convertfrompattern(str(tmp_path / "missing_*.bdo"), str(tmp_path), converter_name="txt", options={})
    assert status == 1
