import logging
import os
from pathlib import Path
from typing import Generator

import pytest

from pymchelper import run

logger = logging.getLogger(__name__)


def is_file_with_magic_bytes(file_path: Path, magic_bytes: bytes) -> bool:
    """Check if file has given type by checking its magic bytes"""
    with open(file_path, 'rb') as f:
        file_header = f.read(len(magic_bytes))

    return file_header == magic_bytes


def is_excel_file(file_path: Path) -> bool:
    """Check if file is Excel file by checking its magic bytes"""
    return is_file_with_magic_bytes(file_path, b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1')


def is_png_file(file_path: Path) -> bool:
    """Check if file is PNG file by checking its magic bytes"""
    return is_file_with_magic_bytes(file_path, b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A')


@pytest.fixture(scope='module')
def shieldhit_single_result_directory() -> Generator[Path, None, None]:
    """Return path to directory with single SHIELD-HIT12A result files"""
    main_dir = Path(__file__).resolve().parent
    yield main_dir / "res" / "shieldhit" / "single"


@pytest.fixture(scope='function')
def shieldhit_single_result_files(shieldhit_single_result_directory) -> Generator[Path, None, None]:
    """Return SHIELD-HIT12A result files as glob generator"""
    return shieldhit_single_result_directory.glob("*.bdo")


@pytest.mark.smoke
@pytest.mark.parametrize("option_name", ["version", "help"])
def test_call_cmd_option(option_name: str):
    """Test if proper zero exit code is returned when option is given."""
    with pytest.raises(SystemExit) as e:
        logger.info("Catching {%s}", e)
        run.main([f'--{option_name}'])
    assert e.value.args[0] == 0


@pytest.mark.smoke
def test_convert_single_to_image(shieldhit_single_result_files: Generator[Path, None, None],
                                 shieldhit_single_result_directory: Path, tmp_path: Path,
                                 monkeypatch: pytest.MonkeyPatch):
    """Test if single BDO file is converted to PNG file"""
    logging.info("Changing working directory to %s", tmp_path)
    monkeypatch.chdir(tmp_path)
    run.main(['image', '--many', f'{shieldhit_single_result_directory}{os.sep}*.bdo'])
    expected_files = tmp_path.glob("*.png")
    assert len(list(expected_files)) == len(list(shieldhit_single_result_files))
    # check if all the files are proper PNG files
    for expected_file_path in expected_files:
        assert is_png_file(expected_file_path)


def test_convert_single_to_excel(shieldhit_single_result_directory: Path, tmp_path: Path,
                                 monkeypatch: pytest.MonkeyPatch):
    """Test if single BDO file is converted to Excel file"""
    logging.info("Changing working directory to %s", tmp_path)
    monkeypatch.chdir(tmp_path)
    run.main(['excel', '--many', f'{shieldhit_single_result_directory}{os.sep}*.bdo'])
    expected_files = tmp_path.glob("*.xls")
    # not all files are converted to excel, we expect 3 files
    assert len(list(expected_files)) == 3
    for expected_file_path in expected_files:
        assert is_excel_file(expected_file_path)
