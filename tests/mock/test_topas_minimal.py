"""Test topas mock"""

import logging
import os
from pathlib import Path
from subprocess import call
from typing import Generator
import numpy as np

import pytest


logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def topas_mock() -> Generator[Path, None, None]:
    """Return path to mock script"""
    yield Path(__file__).parent.parent / "res" / "mocks" / "topas_minimal" / "topas"


@pytest.fixture(scope='module')
def expected_results() -> Generator[dict, None, None]:
    """Return expected result"""
    yield {
        "fluence_bp_protons_xy.csv": {
            "shape": [1, 4, 4],
            "4x4": [
                [0.00177, 0., 0., 0.00088],
                [0.00088, 0.00177, 0., 0.00088],
                [0.00266, 0.00088, 0.00177, 0.00177],
                [0.00088, 0., 0., 0.]
            ]
        },
        "fluence_bp_protons_xy2.csv": {
            "shape": [1, 4, 4],
            "4x4": [
                [0.00177, 0., 0., 0.00088],
                [0., 0.00177, 0.00177, 0.00177],
                [0.00266, 0.00088, 0.00088, 0.],
                [0., 0., 0., 0.]
            ]
        }
    }


@pytest.mark.skipif(os.name == 'nt', reason="Windows not supported")
@pytest.mark.parametrize('output_file', ["fluence_bp_protons_xy.csv", "fluence_bp_protons_xy2.csv"])
def test_topas_mock(tmp_path: Path, output_file: str, expected_results: dict, topas_mock: Path):
    """Test topas mock script"""
    assert topas_mock.exists(), "Topas script does not exist"

    env = append_path_to_environ(topas_mock.parent)
    call("topas", cwd=tmp_path, env=env)  # skipcq: BAN-B607
    output_files = [f.name for f in list(tmp_path.glob("*"))]

    assert output_file in output_files, f"File {output_file} was not created"
    topas_data = from_csv(tmp_path / output_file)
    assert topas_data.any(), "Topas data is None"
    __verify_topas_file(topas_data, expected_results[output_file])


def __verify_topas_file(actual_result: np.ndarray, expected_result: np.ndarray):
    """Compares content of generated topas file with expected values"""

    expected = list(np.around(np.array(expected_result["4x4"]).flatten(), 4))
    result = list(np.around(actual_result.flatten(), 4))
    assert expected == result, "Topas data does not match expected values"


def append_path_to_environ(path: Path) -> dict:
    """Append path to PATH environment variable"""
    env = os.environ.copy()
    if "PATH" in env:
        env["PATH"] = str(path) + os.pathsep + env["PATH"]
    else:
        env["PATH"] = str(path)
    return env


def from_csv(path: Path) -> np.ndarray:
    """Reads csv file and returns numpy array"""
    lines = np.genfromtxt(path, delimiter=',')
    x = lines[:, 0].astype(int).max() + 1
    y = lines[:, 1].astype(int).max() + 1
    z = lines[:, 2].astype(int).max() + 1
    data = np.delete(lines, [0, 1, 2, 4], axis=1)

    return data.reshape((x, y, z))


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
