"""Test mock scripts"""

import logging
import os
from pathlib import Path
from subprocess import call
import unittest

import pytest


from pymchelper.input_output import fromfile
from tests.res.mocks import PATH

logger = logging.getLogger(__name__)


@pytest.mark.skipif(os.name == 'nt', reason="Windows not supported")
def test_fluka_mock(tmp_path: Path):
    """Test fluka mock script"""
    rfluka = PATH / "rfluka"
    assert rfluka.exists(), "rfluka script does not exist"

    expected_files = ["cherenkov001_fort.55", "cherenkov002_fort.55", "cherenkov003_fort.55", "cherenkov004_fort.55"]
    env = append_path_to_environ(os.environ, PATH)
    call("rfluka", cwd=tmp_path, env=env)

    for f in expected_files:
        fp = tmp_path / f
        assert (tmp_path / f).exists(), f"File {f} was not created"
        check_fluka_file(fp)


def check_fluka_file(file: Path):
    # creating empty Detector object and filling it with data read from Fluka file
    fluka_data = fromfile(str(file.resolve()))

    # printing some output on the screen
    logger.info("Fluka bins in X: {:d}, Y: {:d}, Z: {:d}".format(fluka_data.x.n, fluka_data.y.n, fluka_data.z.n))
    logger.info("First bin of fluka data %s", fluka_data.pages[0].data[0, 0, 0, 0, 0])


def append_path_to_environ(env: dict, path: Path) -> dict:
    """Append path to PATH environment variable"""
    if "PATH" in env:
        env["PATH"] = str(path) + os.pathsep + env["PATH"]
    else:
        env["PATH"] = str(path)
    return env


if __name__ == '__main__':
    unittest.main()
