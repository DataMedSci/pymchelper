"""Test fluka mock"""

import logging
import os
import struct
from pathlib import Path
from subprocess import call
from typing import Generator, List
import numpy as np

import pytest
from pymchelper.axis import MeshAxis
from pymchelper.estimator import Estimator
import pymchelper.flair.common.fortran as fortran

from pymchelper.input_output import fromfile
from pymchelper.readers.fluka import data_block_to_array
from pymchelper.run import main

logger = logging.getLogger(__name__)

# records of a USRBIN file with a single detector
FILE_HEADER_RECORD = 0
DETECTOR_HEADER_RECORD = 1
DETECTOR_DATA_RECORD = 2

# USRBIN detector header: number, name, type, score, then low, high, number of bins, bin width for x, y and z, ...
DETECTOR_HEADER_FORMAT = "=i10siiffifffifffififff"
Y_HIGH_FIELD = 9
NUMBER_OF_Y_BINS_FIELD = 10


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


@pytest.fixture(scope='module')
def fluka_outputs(tmp_path_factory: pytest.TempPathFactory, fluka_mock: Path) -> Path:
    """Directory with minimal001_fort.21 (XZ detector) and minimal001_fort.22 (XY detector) made by the rfluka mock"""
    output_dir = tmp_path_factory.mktemp("fluka")
    env = append_path_to_environ(fluka_mock.parent)
    call("rfluka", cwd=output_dir, env=env)  # skipcq: BAN-B607
    return output_dir


@pytest.fixture(scope='module')
def joined_path(fluka_outputs: Path) -> Path:
    """USRBIN file with the XZ detector of minimal001_fort.21 and the XY detector of minimal001_fort.22"""
    xz_records = read_fortran_records(fluka_outputs / "minimal001_fort.21")
    xy_records = read_fortran_records(fluka_outputs / "minimal001_fort.22")
    joined_records = [
        xz_records[FILE_HEADER_RECORD],
        xz_records[DETECTOR_HEADER_RECORD],
        xz_records[DETECTOR_DATA_RECORD],
        xy_records[DETECTOR_HEADER_RECORD],
        xy_records[DETECTOR_DATA_RECORD],
    ]
    path = fluka_outputs / "joined001_fort.23"
    write_fortran_records(path, joined_records)
    return path


@pytest.mark.skipif(os.name == 'nt', reason="Windows not supported")
def test_detectors_with_different_meshes(fluka_outputs: Path, joined_path: Path):
    """Two USRBIN detectors in one file, each page gets the mesh of its own detector"""
    xz_page = fromfile(str(fluka_outputs / "minimal001_fort.21")).pages[0]
    xy_page = fromfile(str(fluka_outputs / "minimal001_fort.22")).pages[0]
    joined = fromfile(str(joined_path))

    assert len(joined.pages) == 2
    for joined_page, single_page in zip(joined.pages, (xz_page, xy_page)):
        assert joined_page.title == single_page.title
        assert joined_page.x == single_page.x
        assert joined_page.y == single_page.y
        assert joined_page.z == single_page.z
        np.testing.assert_array_equal(joined_page.data, single_page.data)

    assert joined.pages[0].data.shape == (4, 1, 4, 1, 1)
    assert joined.pages[1].data.shape == (4, 4, 1, 1, 1)


@pytest.mark.skipif(os.name == 'nt', reason="Windows not supported")
def test_detectors_with_different_number_of_bins(fluka_outputs: Path):
    """XY detector cut from 4 x 4 x 1 to 4 x 2 x 1 bins next to the XZ detector, both pages must be readable"""
    xz_records = read_fortran_records(fluka_outputs / "minimal001_fort.21")
    xy_records = read_fortran_records(fluka_outputs / "minimal001_fort.22")

    # y goes from -5 to 0 cm instead of -5 to 5 cm, so the bin width stays 2.5 cm
    header_fields = list(struct.unpack(DETECTOR_HEADER_FORMAT, xy_records[DETECTOR_HEADER_RECORD]))
    header_fields[NUMBER_OF_Y_BINS_FIELD] = 2
    header_fields[Y_HIGH_FIELD] = 0.0
    cut_header = struct.pack(DETECTOR_HEADER_FORMAT, *header_fields)

    # x changes fastest, so the first 4 x 2 values are the bins with y below 0
    xy_values = np.frombuffer(xy_records[DETECTOR_DATA_RECORD], dtype=np.float32)
    number_of_kept_values = 4 * 2
    cut_values = xy_values[:number_of_kept_values]

    cut_records = [
        xz_records[FILE_HEADER_RECORD],
        xz_records[DETECTOR_HEADER_RECORD],
        xz_records[DETECTOR_DATA_RECORD],
        cut_header,
        cut_values.tobytes(),
    ]
    cut_path = fluka_outputs / "cut001_fort.24"
    write_fortran_records(cut_path, cut_records)

    estimator = fromfile(str(cut_path))

    assert estimator.pages[0].data.shape == (4, 1, 4, 1, 1)
    assert estimator.pages[1].data.shape == (4, 2, 1, 1, 1)
    gev_to_mev = 1000
    np.testing.assert_array_equal(estimator.pages[1].data_raw, cut_values.astype(np.float64) * gev_to_mev)


@pytest.mark.skipif(os.name == 'nt', reason="Windows not supported")
def test_txt_writer_on_detectors_with_different_meshes(fluka_outputs: Path, joined_path: Path, tmp_path: Path):
    """Each page of the joined file gives the same txt output as the file with only its detector"""
    main(["txt", str(fluka_outputs / "minimal001_fort.21"), str(tmp_path / "xz")])
    main(["txt", str(fluka_outputs / "minimal001_fort.22"), str(tmp_path / "xy")])
    main(["txt", str(joined_path), str(tmp_path / "joined")])

    assert (tmp_path / "joined_p1.txt").read_text() == (tmp_path / "xz.txt").read_text()
    assert (tmp_path / "joined_p2.txt").read_text() == (tmp_path / "xy.txt").read_text()


@pytest.mark.skipif(os.name == 'nt', reason="Windows not supported")
def test_hdf_writer_on_detectors_with_different_meshes(fluka_outputs: Path, joined_path: Path, tmp_path: Path):
    """Each dataset of the joined file has the mesh of its own detector"""
    import h5py

    xz_page = fromfile(str(fluka_outputs / "minimal001_fort.21")).pages[0]
    xy_page = fromfile(str(fluka_outputs / "minimal001_fort.22")).pages[0]
    main(["hdf", str(joined_path), str(tmp_path / "joined")])

    with h5py.File(tmp_path / "joined.h5", 'r') as hdf_file:
        for dataset_name, single_page in (("data_0", xz_page), ("data_1", xy_page)):
            attributes = hdf_file[dataset_name].attrs
            assert hdf_file[dataset_name].shape == single_page.data.shape
            for axis_name in ("x", "y", "z"):
                axis = getattr(single_page, axis_name)
                assert attributes[f"{axis_name}axis_n"] == axis.n
                assert attributes[f"{axis_name}axis_min"] == axis.min_val
                assert attributes[f"{axis_name}axis_max"] == axis.max_val
                assert attributes[f"{axis_name}axis_name"] == axis.name


@pytest.mark.skipif(os.name == 'nt', reason="Windows not supported")
def test_inspect_prints_mesh_of_each_page(joined_path: Path, capsys: pytest.CaptureFixture):
    """Mesh is printed once per page, with the number of bins of its own detector"""
    main(["inspect", str(joined_path)])
    output_lines = capsys.readouterr().out.splitlines()

    x_axis_lines = []
    for line in output_lines:
        if line.split(":")[0].strip() == "x":
            x_axis_lines.append(line)

    assert len(x_axis_lines) == 2
    for line in x_axis_lines:
        assert line.startswith("\t")
        assert "n=4," in line


def test_data_block_to_array():
    """Same values as unpacking one float at a time, as float64 and writable"""
    values = np.random.default_rng(0).random(1000).astype(np.float32)
    data_block = values.tobytes()

    result = data_block_to_array(data_block)

    expected = np.array(struct.unpack(f"={values.size}f", data_block))
    np.testing.assert_array_equal(result, expected)
    assert result.dtype == np.float64
    assert result.flags.writeable


def __verify_fluka_file(actual_result: Estimator, expected_result: dict):
    """Compares content of generated fluka file with expected values"""
    page = actual_result.pages[0]
    assert expected_result["shape"] == [page.x.n, page.y.n, page.z.n]
    assert len(actual_result.pages) == 1
    assert expected_result['name'] in actual_result.pages[0].name
    for axis_name, value in expected_result["axis"].items():
        verify_axis(page.__getattribute__(axis_name), value)

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


def read_fortran_records(file_path: Path) -> List[bytes]:
    """Read all records of a Fortran unformatted file, without their length markers"""
    records = []
    with open(file_path, "rb") as file:
        record = fortran.read(file)
        while record is not None:
            records.append(record)
            record = fortran.read(file)
    return records


def write_fortran_records(file_path: Path, records: List[bytes]) -> None:
    """Write records to a Fortran unformatted file, each with its length markers"""
    with open(file_path, "wb") as file:
        for record in records:
            fortran.write(file, record)
