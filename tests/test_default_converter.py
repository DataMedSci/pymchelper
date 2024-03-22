import numpy as np
import pytest
from typing import List, Tuple
from pymchelper.estimator import Estimator, ErrorEstimate
from pymchelper.input_output import fromfilelist, fromfile


@pytest.fixture
def file_list() -> List[str]:
    """
    Fixture to generate a list of file paths for testing.

    Returns:
        List[str]: A list of file paths for the test files.
    """
    return [f"tests/res/shieldhit/generated/many/msh/aen_0_p000{i}.bdo" for i in range(1, 4)]


@pytest.fixture
def estimator_list(file_list: List[str]) -> List[Estimator]:
    """
    Fixture to prepare a list of estimator objects based on a given list of file paths.

    Args:
        file_list (List[str]): A list of file paths from which to load the estimator objects.

    Returns:
        List[Estimator]: A list of estimator objects loaded from the given file paths.
    """
    return [fromfile(file_path) for file_path in file_list]


@pytest.mark.parametrize("error", list(ErrorEstimate))
@pytest.mark.parametrize("nan", [False, True])
def test_normal_numbers_with_params(file_list: List[str], estimator_list: List[Estimator], error: ErrorEstimate,
                                    nan: bool) -> None:
    """
    Test the error calculations for merged estimators under various conditions.

    This function tests the error calculations by merging a list of estimators
    with specified error handling and NaN inclusion options. It verifies that the
    calculated mean values are consistent with manually calculated mean values from
    the individual estimators. It also checks that the error values (standard deviation
    or standard error) are calculated correctly, according to the specified error type.

    Args:
        file_list (List[str]): A list of file paths used to create the estimator objects.
        estimator_list (List[Estimator]): A list of estimator objects created from the file paths.
        error (ErrorEstimate): The type of error calculation to apply when merging the estimators.
        nan (bool): Flag indicating whether to include NaN values in the error calculations.
    """
    merged_estimators = fromfilelist(file_list, error=error, nan=nan)

    for page_no, page in enumerate(merged_estimators.pages):
        mean_value = np.mean([est.pages[page_no].data_raw for est in estimator_list])
        assert mean_value == page.data_raw, f"Mean value calculation mismatch for error={error}, nan={nan}"

    if error == ErrorEstimate.none:
        for page in merged_estimators.pages:
            assert page.error_raw is None, f"Error value should be None for error={error}, nan={nan}, file_list={file_list}"
    if error in (ErrorEstimate.stddev, ErrorEstimate.stderr):
        for page_no, page in enumerate(merged_estimators.pages):
            error_value = np.std([est.pages[page_no].data_raw for est in estimator_list], ddof=1)
            if error == ErrorEstimate.stderr:
                error_value /= np.sqrt(len(estimator_list))
            assert np.allclose(error_value,
                               page.error_raw), f"Error value calculation mismatch for error={error}, nan={nan}"
