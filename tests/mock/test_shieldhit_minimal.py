"""Test shieldhit mock"""

import logging
import os
from pathlib import Path
from subprocess import call
from typing import Generator
import numpy as np

import pytest
from pymchelper.estimator import Estimator


from pymchelper.input_output import fromfile

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def shieldhit_mock() -> Generator[Path, None, None]:
    """Return path to mock script"""
    yield Path(__file__).parent.parent / "res" / "mocks" / "shieldhit_minimal" / "shieldhit"


@pytest.fixture(scope='module')
def expected_results() -> Generator[dict, None, None]:
    """Return expected result"""
    yield {
        "mesh.bdo": {
            "shape": [4, 1, 4],
            "4x4": [
                [0.31776, 0.54793, 0.15288, 0.0],
                [0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0]
            ]
        },
        "fluence.bdo": {
            "shape": [4, 1, 4],
            "4x4": [
                [0.05093, 0.05099, 0.0036, 0.],
                [0., 0., 0., 0.],
                [0., 0., 0., 0.],
                [0., 0., 0., 0.]
            ]
        }
    }


@pytest.mark.skipif(os.name == 'nt', reason="Windows not supported")
@pytest.mark.parametrize('output_file', ["mesh.bdo", "fluence.bdo"])
def test_shieldhit_mock(tmp_path: Path, output_file: str, expected_results: dict, shieldhit_mock: Path):
    """Test shieldhit mock script"""
    assert shieldhit_mock.exists(), "shieldhit script does not exist"

    env = append_path_to_environ(shieldhit_mock.parent)
    call("shieldhit", cwd=tmp_path, env=env)  # skipcq: BAN-B607
    output_files = [f.name for f in list(tmp_path.glob("*"))]

    assert output_file in output_files, f"File {output_file} was not created"
    shieldhit_data = fromfile(str((tmp_path / output_file).resolve()))
    assert shieldhit_data, "Shieldhit data is None"
    __verify_shieldhit_file(shieldhit_data, expected_results[output_file])


def __verify_shieldhit_file(actual_result: Estimator, expected_result: dict):
    """Compares content of generated shieldhit file with expected values"""
    assert expected_result["shape"] == [actual_result.x.n, actual_result.y.n, actual_result.z.n]

    expected = list(np.around(np.array(expected_result["4x4"]).flatten(), 4))
    result = list(np.around(np.array(actual_result.pages[0].data).flatten(), 4))
    assert expected == result, "Shieldhit data does not match expected values"


def append_path_to_environ(path: Path) -> dict:
    """Append path to PATH environment variable"""
    env = os.environ.copy()
    if "PATH" in env:
        env["PATH"] = str(path) + os.pathsep + env["PATH"]
    else:
        env["PATH"] = str(path)
    return env


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
