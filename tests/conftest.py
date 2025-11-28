import logging
import platform
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Generator
import zipfile

import pytest
import requests

sh12a_ver = '1.1.0'
linux_sh12a_demo_url = f'https://shieldhit.org/download/DEMO/shield_hit12a_x86_64_demo_gfortran_v{sh12a_ver}.tar.gz'
windows_sh12a_demo_url = f'https://shieldhit.org/download/DEMO/shield_hit12a_win64_demo_v{sh12a_ver}.zip'


def extract_shieldhit_from_tar_gz(archive_path: Path, 
                                  unpacking_dir: Path, 
                                  member_name: str, 
                                  installation_dir: Path) -> None:
    """Extracts a single file from a tar.gz archive"""
    with tarfile.open(archive_path, "r:gz") as tar:
        # print all members
        for member in tar.getmembers():
            if Path(member.name).name == member_name and Path(member.name).parent.name == 'bin':
                logging.info("Extracting %s", member.name)
                tar.extract(member, unpacking_dir)
                # move to installation path
                local_file = Path(unpacking_dir) / member.name
                logging.info("Moving %s to %s", local_file, installation_dir)
                shutil.move(local_file, installation_dir / member_name)


def extract_shieldhit_from_zip(archive_path: Path, 
                               unpacking_dir: Path, 
                               member_name: str, 
                               installation_dir: Path) -> None:
    """Extracts a single file from a zip archive"""
    with zipfile.ZipFile(archive_path) as zip_handle:
        # print all members
        for member in zip_handle.infolist():
            logging.info("Member: %s", member.filename)
            if Path(member.filename).name == member_name:
                logging.info("Extracting %s", member.filename)
                zip_handle.extract(member, unpacking_dir)
                # move to installation path
                local_file_path = Path(unpacking_dir) / member.filename
                destination_file_path = installation_dir / member_name
                logging.info("Moving %s to %s", local_file_path, installation_dir)
                # move file from temporary directory to installation path using shutils
                if not destination_file_path.exists():
                    shutil.move(local_file_path, destination_file_path)


def download_shieldhit_demo_version(installation_dir: Path) -> None:
    """Download shieldhit demo version from shieldhit.org"""
    demo_version_url = linux_sh12a_demo_url
    # check if working on Windows
    if platform.system() == 'Windows':
        demo_version_url = windows_sh12a_demo_url

    # create temporary directory and download
    with tempfile.TemporaryDirectory() as tmpdir_name:
        logging.info("Downloading from %s to %s", demo_version_url, tmpdir_name)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT x.y; rv:10.0) Gecko/20100101 Firefox/10.0'}
        response = requests.get(demo_version_url, headers=headers)
        temp_file_archive = Path(tmpdir_name) / Path(demo_version_url).name
        with open(temp_file_archive, 'wb') as file_handle:
            file_handle.write(response.content)
        logging.info("Downloaded to %s with size %s bytes", temp_file_archive, temp_file_archive.stat().st_size)

        # extract
        logging.info("Extracting %s to %s", temp_file_archive, installation_dir)
        if temp_file_archive.suffix == '.gz':
            extract_shieldhit_from_tar_gz(archive_path=temp_file_archive,
                                          unpacking_dir=Path(tmpdir_name),
                                          member_name='shieldhit',
                                          installation_dir=installation_dir)
        elif temp_file_archive.suffix == '.zip':
            extract_shieldhit_from_zip(archive_path=temp_file_archive,
                                       unpacking_dir=Path(tmpdir_name),
                                       member_name='shieldhit.exe',
                                       installation_dir=installation_dir)


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


@pytest.fixture(scope='session')
def shieldhit_demo_binary_installed(shieldhit_installation_dir: Path, shieldhit_binary_path: Path):
    """Checks if SHIELD-HIT12A binary is installed and installs it if necessary"""
    logging.info("SHIELDHIT binary path %s", shieldhit_binary_path)

    if not shieldhit_binary_path.exists():
        logging.info("SHIELDHIT binary not found, downloading and installing")
        shieldhit_installation_dir.mkdir(parents=True, exist_ok=True)
        download_shieldhit_demo_version(shieldhit_installation_dir)
