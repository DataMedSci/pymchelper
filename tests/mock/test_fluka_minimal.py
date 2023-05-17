"""Test mock scripts"""

import logging
import os
from pathlib import Path
from subprocess import call
import numpy as np

import pytest
from pymchelper.estimator import Estimator


from pymchelper.input_output import fromfile

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def fluka_mock() -> Path:
    """Return path to mock script"""
    return Path(__file__).parent.parent / "res" / "mocks" / "fluka_minimal" / "rfluka"


@pytest.fixture(scope='module')
def expected_results() -> dict:
    """Return expected result"""
    return {
        "minimal001_fort.21": {
            "shape": [4, 1, 4],
            "4x4": [
                [0., 0., 0., 0.],
                [0., 0.00146468, 0.00169978, 0.],
                [0.00090805, 0., 0., 0.],
                [0, 0., 0., 0.]
            ]
        },
        "minimal001_fort.22": {
            "shape": [4, 4, 1],
            "4x4": [
                [0.00047575, 0., 0., 0.],
                [0., 0.00188021, 0.00166488, 0.],
                [0., 0.0010242, 0.00105254, 0.],
                [0., 0., 0., 0.]
            ]
        }
    }


@pytest.mark.skipif(os.name == 'nt', reason="Windows not supported")
@pytest.mark.parametrize('output_file', ["minimal001_fort.21", "minimal001_fort.22"])
def test_fluka_mock(tmp_path: Path, output_file: str, expected_results: dict, fluka_mock: Path):
    """Test fluka mock script"""
    assert fluka_mock.exists(), "rfluka script does not exist"

    env = append_path_to_environ(fluka_mock.parent)
    call("rfluka", cwd=tmp_path, env=env)
    output_files = [f.name for f in list(tmp_path.glob("*"))]

    assert output_file in output_files, f"File {output_file} was not created"
    fluka_data = fromfile(str((tmp_path / output_file).resolve()))
    assert fluka_data, "Fluka data is None"
    __verify_fluka_file(fluka_data, expected_results[output_file])


def __verify_fluka_file(actual_result: Estimator, expected_result: dict):
    """Compares content of generated fluka file with expected values"""
    assert (expected_result["shape"] == [actual_result.x.n, actual_result.y.n, actual_result.z.n])

    expected = list(np.around(np.array(expected_result["4x4"]).flatten(), 4))
    result = list(np.around(np.array(actual_result.pages[0].data).flatten(), 4))
    assert expected == result, "Fluka data does not match expected values"


def append_path_to_environ(path: Path) -> dict:
    """Append path to PATH environment variable"""
    env = os.environ.copy()
    if "PATH" in env:
        env["PATH"] = str(path) + os.pathsep + env["PATH"]
    else:
        env["PATH"] = str(path)
    return env
