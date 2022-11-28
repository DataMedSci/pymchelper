import logging
import pytest
import unittest

from pathlib import Path

import pymchelper.utils.radiotherapy.plan

logger = logging.getLogger(__name__)


# @pytest.fixture(scope='module')
# def beam_model_path() -> Path:
#     return Path('tests', 'res', 'pld', 'beam_model_generic.csv')

beam_model = Path('tests', 'res', 'pld', 'beam_model_generic.csv')

input_files = [
    Path('tests', 'res', 'pld', 'test.pld'),
    Path('tests', 'res', 'dicom', 'RN.1.2.246.352.71.5.37402163639.162240.20220929101251.dcm'),
    Path('tests', 'res', 'dicom', 'RN.1.2.246.352.71.5.361940808526.37240.20200311150225.dcm')
]

output_file = "sobp.dat"


def test_call_cmd_no_option():
    """Test calling pymchelper with no options."""
    with pytest.raises(SystemExit) as e:
        logger.info("Catching {:s}".format(str(e)))
        pymchelper.utils.radiotherapy.plan.main([])
        assert e.value == 2


@pytest.mark.parametrize("option_name", ["version", "help"])
def test_call_cmd_option(option_name: str):
    """Test calling pymchelper with no options."""
    with pytest.raises(SystemExit) as e:
        logger.info("Catching {:s}".format(str(e)))
        pymchelper.utils.radiotherapy.plan.main([])
        assert e.value == 0


@pytest.mark.parametrize("input_file_path", input_files)
def test_plan_no_bm(input_file_path: Path):
    """Test plan loading without beam model."""

    exit_code = pymchelper.utils.radiotherapy.plan.main([str(input_file_path)])
    assert exit_code == 0

    # expected_output_file_path = Path(output_file)
    # assert expected_output_file_path.exists()


# @pytest.mark.parametrize("input_file_path", input_files)
# def test_plan_bm(input_file_path: Path):
#     """Test plan loading with beam model."""
#     inp = f"{input_file_path} -v -b {beam_model}"
#     print(inp)
#     exit_code = pymchelper.utils.radiotherapy.plan.main([inp])
#     assert exit_code == 0


if __name__ == '__main__':
    unittest.main()
