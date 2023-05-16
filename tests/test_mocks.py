"""Test mock scripts"""

import logging
import os
from pathlib import Path
from subprocess import call
import unittest
import numpy as np

import pytest
from pymchelper.estimator import Estimator


from pymchelper.input_output import fromfile

__MOCKS_PATH = Path(__file__).parent / "res" / "mocks"

logger = logging.getLogger(__name__)


__EXPECTED_FLUKA_RESULTS = {
    "minimal001_fort.21": {
        "shape": [4, 1, 4],
        "4x4": [
            [0., 0., 0., 0.],
            [0., 0.00146468, 0.00169978, 0.],
            [0.00090805, 0., 0.,0.],
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
@pytest.mark.parametrize('output_file', __EXPECTED_FLUKA_RESULTS.keys())
def test_fluka_mock(tmp_path: Path, output_file: str):
    """Test fluka mock script"""
    rfluka = __MOCKS_PATH / "fluka_minimal" / "rfluka"
    assert rfluka.exists(), "rfluka script does not exist"

    env = append_path_to_environ(os.environ.copy(), __MOCKS_PATH / "fluka_minimal")
    call("rfluka", cwd=tmp_path, env=env)
    output_files = [f.name for f in list(tmp_path.glob("*"))]

    assert output_file in output_files, f"File {output_file} was not created"
    fluka_data = fromfile(str((tmp_path / output_file).resolve()))
    assert fluka_data, "Fluka data is None"
    __verify_fluka_file(fluka_data, output_file)


def __verify_fluka_file(fluka_data: Estimator , filename: str):
    """Compares content of generated fluka file with expected values"""
    assert (__EXPECTED_FLUKA_RESULTS[filename]["shape"] == [fluka_data.x.n, fluka_data.y.n, fluka_data.z.n])

    expected = list(np.around(np.array(__EXPECTED_FLUKA_RESULTS[filename]["4x4"]).flatten(), 4))
    result = list(np.around(np.array(fluka_data.pages[0].data).flatten(), 4))
    assert expected == result, "Fluka data does not match expected values"


def append_path_to_environ(env: dict, path: Path) -> dict:
    """Append path to PATH environment variable"""
    if "PATH" in env:
        env["PATH"] = str(path) + os.pathsep + env["PATH"]
    else:
        env["PATH"] = str(path)
    return env


if __name__ == '__main__':
    unittest.main()
