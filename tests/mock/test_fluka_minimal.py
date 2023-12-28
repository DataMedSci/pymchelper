"""Test fluka mock"""

import logging
import os
from pathlib import Path
from subprocess import call
from typing import Generator
import numpy as np

import pytest
from pymchelper.axis import MeshAxis
from pymchelper.estimator import Estimator


from pymchelper.input_output import fromfile

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def fluka_mock() -> Generator[Path, None, None]:
    """Return path to mock script"""
    yield Path(__file__).parent.parent / "res" / "mocks" / "fluka_minimal" / "rfluka"


@pytest.fixture(scope='module')
def expected_results() -> dict:
    """Return expected result"""
    yield {
        "minimal001_fort.21": {
            "shape": [4, 1, 4],
            "4x4": [
                [0., 0., 0., 0.],
                [0., 1.46468, 1.69978, 0.],
                [0.9081, 0., 0., 0.],
                [0, 0., 0., 0.]
            ],
            "name": "ENERGY",
            "axis": {
                "x": {
                    "name": "Position (X)",
                    "unit": "cm",
                },
                "y": {
                    "name": "Position (Y)",
                    "unit": "cm",
                },
                "z": {
                    "name": "Position (Z)",
                    "unit": "cm",
                },
            }
        },
        "minimal001_fort.22": {
            "shape": [4, 4, 1],
            "4x4": [
                [0.4757, 0., 0., 0.],
                [0., 1.88021, 1.66488, 0.],
                [0., 1.0242, 1.05254, 0.],
                [0., 0., 0., 0.]
            ],
            "name": "ENERGY",
            "axis": {
                "x": {
                    "name": "Position (X)",
                    "unit": "cm",
                },
                "y": {
                    "name": "Position (Y)",
                    "unit": "cm",
                },
                "z": {
                    "name": "Position (Z)",
                    "unit": "cm",
                },
            }
        }
    }


@pytest.mark.skipif(os.name == 'nt', reason="Windows not supported")
@pytest.mark.parametrize('output_file', ["minimal001_fort.21", "minimal001_fort.22"])
def test_fluka_mock(tmp_path: Path, output_file: str, expected_results: dict, fluka_mock: Path):
    """Test fluka mock script"""
    assert fluka_mock.exists(), "rfluka script does not exist"

    env = append_path_to_environ(fluka_mock.parent)
    call("rfluka", cwd=tmp_path, env=env)  # skipcq: BAN-B607
    output_files = [f.name for f in list(tmp_path.glob("*"))]

    assert output_file in output_files, f"File {output_file} was not created"
    fluka_data = fromfile(str((tmp_path / output_file).resolve()))
    assert fluka_data, "Fluka data is None"
    __verify_fluka_file(fluka_data, expected_results[output_file])


def __verify_fluka_file(actual_result: Estimator, expected_result: dict):
    """Compares content of generated fluka file with expected values"""
    assert expected_result["shape"] == [actual_result.x.n, actual_result.y.n, actual_result.z.n]
    assert len(actual_result.pages) == 1
    assert expected_result['name'] in actual_result.pages[0].name
    for axis_name, value in expected_result["axis"].items():
        verify_axis(actual_result.__getattribute__(axis_name), value)

    expected = list(np.around(np.array(expected_result["4x4"]).flatten(), 4))
    result = list(np.around(np.array(actual_result.pages[0].data).flatten(), 4))
    assert expected == result, "Fluka data does not match expected values"


def verify_axis(axis: MeshAxis, expected_axis: dict):
    """Compares axis of generated fluka file with expected values"""
    assert axis.name == expected_axis["name"]
    assert axis.unit == expected_axis["unit"]


def append_path_to_environ(path: Path) -> dict:
    """Append path to PATH environment variable"""
    env = os.environ.copy()
    if "PATH" in env:
        env["PATH"] = str(path) + os.pathsep + env["PATH"]
    else:
        env["PATH"] = str(path)
    return env
