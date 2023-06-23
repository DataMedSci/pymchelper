import logging
from pathlib import Path
from examples import generate_detect_shieldhit, generate_fluka_input
from pymchelper.flair import Input

import pytest

logger = logging.getLogger(__name__)


def test_generate_shieldhit_input(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test if shieldhit input is generated correctly"""
    logging.info("Changing working directory to %s", tmp_path)
    monkeypatch.chdir(tmp_path)
    generate_detect_shieldhit.main()

    expected_file = Path('detect.dat')
    assert expected_file.is_file()
    assert expected_file.stat().st_size > 0

    # check if only one file is created in current directory
    assert len(list(tmp_path.glob('*'))) == 1


def test_generate_fluka_input(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test if fluka input is generated correctly"""
    logging.info("Changing working directory to %s", tmp_path)
    monkeypatch.chdir(tmp_path)
    generate_fluka_input.main()

    expected_file = Path('fl_sim.inp')
    assert expected_file.is_file()
    assert expected_file.stat().st_size > 0

    # check if only one file is created in current directory
    assert len(list(tmp_path.glob('*'))) == 1

    fluka_input = Input.Input()
    fluka_input.read(str(expected_file))

    logger.info("checking presence of RANDOMIZ card")
    assert "RANDOMIZ" in fluka_input.cards

    logger.info("checking if there is only one RANDOMIZ card ")
    assert len(fluka_input.cards["RANDOMIZ"]) == 1

    logger.info("checking if RNG setting is correct ")
    assert fluka_input.cards["RANDOMIZ"][0].whats()[2] == 137

    logger.info("checking presence of USRBIN cards")
    assert "USRBIN" in fluka_input.cards

    logger.info("checking if there are 8 USRBIN cards")
    assert len(fluka_input.cards["USRBIN"]) == 8
