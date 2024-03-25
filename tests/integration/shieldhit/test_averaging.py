import logging
from pathlib import Path
from typing import Generator

import numpy as np
import pytest

from pymchelper.input_output import fromfile, fromfilelist

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def averaging_bdos_directory(main_dir) -> Generator[Path, None, None]:
    """Path to directory with BDO files"""
    yield main_dir / "res" / "shieldhit" / "averaging"


@pytest.fixture(scope='function')
def small_stat_bdo_pattern() -> Generator[str, None, None]:
    """Part of filename denoting small statistics BDO file"""
    yield "_000?.bdo"


@pytest.fixture(scope='function')
def large_stat_bdo_pattern() -> Generator[str, None, None]:
    """Part of filename denoting large statistics BDO file"""
    yield "_001?.bdo"


@pytest.mark.parametrize("output_type", [
    "normalisation-1_aggregation-none", "normalisation-2_aggregation-sum", "normalisation-3_aggregation-mean",
    "normalisation-4_aggregation-concat", "normalisation-5_aggregation-mean"
])
def test_aggregating_equal_stats(averaging_bdos_directory, small_stat_bdo_pattern, large_stat_bdo_pattern, output_type):
    """
    Check if data from averaged estimator is equal to data from all estimators
    In both sets of data, the same number of primary particles was used
    Therefore we can use simple averaging
    """

    for stat_pattern in (small_stat_bdo_pattern, large_stat_bdo_pattern):
        bdo_file_pattern = f"{output_type}{stat_pattern}"
        input_file_list = list(averaging_bdos_directory.glob(bdo_file_pattern))

        averaged_estimators = fromfilelist(input_file_list=[str(path) for path in input_file_list])
        assert len(averaged_estimators.pages) > 0

        list_of_estimators_for_each_file = [fromfile(str(path)) for path in input_file_list]
        assert len(list_of_estimators_for_each_file) > 0

        for page_id, page in enumerate(averaged_estimators.pages):
            list_of_entries_to_aggregate = []
            for estimator in list_of_estimators_for_each_file:
                assert len(estimator.pages) > page_id
                list_of_entries_to_aggregate.append(estimator.pages[page_id].data)

            if "mean" in output_type:
                assert np.average(list_of_entries_to_aggregate) == pytest.approx(page.data)
                assert np.std(list_of_entries_to_aggregate, ddof=1, axis=0) / np.sqrt(
                    len(input_file_list)) == pytest.approx(page.error)
            elif "sum" in output_type:
                assert np.sum(list_of_entries_to_aggregate) == pytest.approx(page.data)
                assert page.error is None
            elif "none" in output_type:
                assert list_of_entries_to_aggregate[0] == pytest.approx(page.data)
                assert page.error is None
            elif "concat" in output_type:
                assert np.concatenate(list_of_entries_to_aggregate, axis=1) == pytest.approx(page.data)
                assert page.error is None
