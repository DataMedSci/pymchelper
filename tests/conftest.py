import platform
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope='session')
def main_dir() -> Generator[Path, None, None]:
    """Return path to main directory of this file"""
    yield Path(__file__).resolve().parent


@pytest.fixture(scope='session')
def shieldhit_installation_dir() -> Generator[Path, None, None]:
    """Returns the installation directory for SHIELD-HIT12A"""
    main_dir = Path(__file__).resolve().parent
    installation_path = main_dir / 'res' / 'shieldhit' / 'executable'
    yield installation_path


@pytest.fixture(scope='session')
def shieldhit_binary_filename() -> Generator[Path, None, None]:
    """Returns the installation directory for SHIELD-HIT12A"""
    filename = Path('shieldhit')
    # check if working on Windows
    if platform.system() == 'Windows':
        filename = Path('shieldhit.exe')
    yield filename


@pytest.fixture(scope='session')
def shieldhit_binary_path(shieldhit_installation_dir: Path,
                          shieldhit_binary_filename: Path) -> Generator[Path, None, None]:
    """Returns the path to the SHIELD-HIT12A binary"""
    yield shieldhit_installation_dir / shieldhit_binary_filename
