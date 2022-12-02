import logging
import shutil
from typing import Union
import pytest
import unittest

from pathlib import Path

import pymchelper.utils.radiotherapy.plan

logger = logging.getLogger(__name__)

beam_model_path = Path('tests', 'res', 'pld', 'beam_model_generic.csv')

input_files = {
    'test.pld': Path('tests', 'res', 'pld', 'test.pld'),
    'rn_2Gy.dcm': Path('tests', 'res', 'dicom', 'RN.1.2.246.352.71.5.37402163639.162240.20220929101251.dcm'),
    'rn_100Gy.dcm': Path('tests', 'res', 'dicom', 'RN.1.2.246.352.71.5.361940808526.37240.20200311150225.dcm')
}

output_file = "sobp.dat"


def test_call_cmd_no_option():
    """Test calling pymchelper with no options."""
    with pytest.raises(SystemExit) as e:
        logger.info("Catching: ", e)
        pymchelper.utils.radiotherapy.plan.main([])
        assert e.value == 2


@pytest.mark.parametrize("option_name", ["version", "help"])
def test_call_cmd_option(option_name: str):
    """Test calling pymchelper with no options."""
    with pytest.raises(SystemExit) as e:
        logger.info("Catching: ", e)
        pymchelper.utils.radiotherapy.plan.main([])
        assert e.value == 0


@pytest.mark.parametrize("input_file_path", input_files.values(), ids=input_files.keys())
@pytest.mark.parametrize("beam_model_path", [beam_model_path, None], ids=[beam_model_path.stem, "no_beam_model"])
def test_generate_plan(input_file_path: Path, beam_model_path: Union[Path, None], monkeypatch: pytest.MonkeyPatch,
                       tmp_path: Path, capsys: pytest.CaptureFixture):
    """Test plan loading with and without beam model."""

    expected_output_file_path = Path(output_file)

    # prepare command line arguments, we do it here as we need to have absolute paths
    # later on we will change the current directory to tmp_path and won't be able to resolve them
    cmd_line_args = [str(input_file_path.resolve())]
    if beam_model_path is not None:
        cmd_line_args.append('-b')
        cmd_line_args.append(str(beam_model_path.resolve()))

    # temporary change working directory to newly created temporary directory
    # this ensures that we run the test where the output file was not generated yet
    monkeypatch.chdir(tmp_path)

    # output file should not exist yet prior to running the test
    assert not expected_output_file_path.exists()

    # run the test
    exit_code = pymchelper.utils.radiotherapy.plan.main(cmd_line_args)
    assert exit_code == 0

    # check that nothing was logged to the output and error streams
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""

    # check if output file exists
    assert expected_output_file_path.exists()
    assert expected_output_file_path.is_file()
    # check if file is not empty
    assert expected_output_file_path.stat().st_size > 0

    # go back to original working directory
    monkeypatch.chdir(Path.cwd())

    # remove tmp_path directory and all its contents
    shutil.rmtree(tmp_path)


@pytest.mark.parametrize("input_file_path", input_files.values(), ids=input_files.keys())
@pytest.mark.parametrize("beam_model_path", [beam_model_path, None], ids=[beam_model_path.stem, "no_beam_model"])
def test_debug_mode(input_file_path: Path, beam_model_path: Union[Path, None], monkeypatch: pytest.MonkeyPatch,
                    tmp_path: Path, capsys: pytest.CaptureFixture):
    """Test plan loading with and without beam model."""

    expected_output_file_path = Path(output_file)

    # prepare command line arguments, we do it here as we need to have absolute paths
    # later on we will change the current directory to tmp_path and won't be able to resolve them
    cmd_line_args = [str(input_file_path.resolve())]
    cmd_line_args.append('-d')
    if beam_model_path is not None:
        cmd_line_args.append('-b')
        cmd_line_args.append(str(beam_model_path.resolve()))

    # temporary change working directory to newly created temporary directory
    # this ensures that we run the test where the output file was not generated yet
    monkeypatch.chdir(tmp_path)

    # output file should not exist yet prior to running the test
    assert not expected_output_file_path.exists()

    # run the test
    exit_code = pymchelper.utils.radiotherapy.plan.main(cmd_line_args)
    assert exit_code == 0

    # check that nothing was logged to the error stream
    captured = capsys.readouterr()
    assert captured.err == ""

    # check that something was logged to the output stream
    assert "Diagnostics:" in captured.out
    assert "Plan label" in captured.out

    # check if output file exists
    assert not expected_output_file_path.exists()

    # go back to original working directory
    monkeypatch.chdir(Path.cwd())

    # remove tmp_path directory and all its contents
    shutil.rmtree(tmp_path)
