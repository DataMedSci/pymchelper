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
def test_averaging_equal_stats(averaging_bdos_directory, small_stat_bdo_pattern, large_stat_bdo_pattern, output_type):
    for stat_pattern in (small_stat_bdo_pattern, large_stat_bdo_pattern):
        bdo_file_pattern = f"{output_type}{stat_pattern}"
        input_file_list = list(averaging_bdos_directory.glob(bdo_file_pattern))

        averaged_estimators = fromfilelist(input_file_list=[str(path) for path in input_file_list])
