import logging
from pathlib import Path
from typing import Generator

import numpy as np
import pytest

from pymchelper.input_output import fromfile, fromfilelist

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def shieldhit_multiple_result_directory() -> Generator[Path, None, None]:
    """Return path to directory with single SHIELD-HIT12A result files"""
    main_dir = Path(__file__).resolve().parent
    yield main_dir / "res" / "shieldhit" / "generated" / "many" / "msh"


@pytest.fixture(scope='function')
def shieldhit_multiple_result_pattern() -> Generator[str, None, None]:
    """Return SHIELD-HIT12A result files as glob generator"""
    yield "aen_x_al0*.bdo"


def test_averaging(shieldhit_multiple_result_pattern, shieldhit_multiple_result_directory):
    """Test if averaging of multiple SHIELD-HIT12A result files works"""
    input_file_list = list(shieldhit_multiple_result_directory.glob(shieldhit_multiple_result_pattern))
    assert len(input_file_list) == 3
    averaged_data = fromfilelist(input_file_list=[str(path) for path in input_file_list])
    assert averaged_data is not None
    assert len(averaged_data.pages) == 1
    logger.info("Averaged data: %s", averaged_data.pages[0].data[5, 0, 0, 0, 0].max())
    list_of_entries_to_average = []
    for input_file_path in input_file_list:
        file_data = fromfile(str(input_file_path))
        assert file_data is not None
        assert len(file_data.pages) == 1
        logger.info("File data: %s", file_data.pages[0].data[5, 0, 0, 0, 0].max())
        list_of_entries_to_average.append(file_data.pages[0].data[5, 0, 0, 0, 0])
    assert len(list_of_entries_to_average) == 3
    assert np.average(list_of_entries_to_average, axis=0) == pytest.approx(averaged_data.pages[0].data[5, 0, 0, 0, 0],
                                                                           rel=1e-9)
