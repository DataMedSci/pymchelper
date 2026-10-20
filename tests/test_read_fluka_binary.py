import struct
import subprocess
import sys
from pathlib import Path
from typing import List

import numpy as np
import pytest

from pymchelper.axis import AxisId
from pymchelper.input_output import fromfile
from pymchelper.readers.fluka import data_block_to_array

DETECTOR_HEADER_FORMAT = "=i10siiffifffifffififff"


def read_records(file_path: Path) -> List[bytes]:
    """Split a Fortran unformatted file into records, each with its length markers"""
    content = file_path.read_bytes()
    records = []
    position = 0
    while position < len(content):
        record_length = struct.unpack("=i", content[position:position + 4])[0]
        records.append(content[position:position + 8 + record_length])
        position += 8 + record_length
    return records


def make_record(payload: bytes) -> bytes:
    """Wrap payload in Fortran record length markers"""
    length_marker = struct.pack("=i", len(payload))
    return length_marker + payload + length_marker


@pytest.fixture(scope="module")
def mock_outputs(tmp_path_factory) -> Path:
    """Directory with minimal001_fort.21 (XZ mesh) and minimal001_fort.22 (XY mesh) from the rfluka mock"""
    if sys.platform == "win32":
        pytest.skip("simulator mocks don't work on Windows")
    output_dir = tmp_path_factory.mktemp("fluka")
    rfluka_mock = Path("tests") / "res" / "mocks" / "fluka_minimal" / "rfluka"
    subprocess.run(["bash", str(rfluka_mock.absolute())], cwd=output_dir, check=True, capture_output=True)
    return output_dir


def test_detectors_with_different_meshes(mock_outputs: Path):
    """Two USRBIN detectors in one unit, each page gets the mesh of its own detector"""
    xz_records = read_records(mock_outputs / "minimal001_fort.21")
    xy_records = read_records(mock_outputs / "minimal001_fort.22")
    joined_path = mock_outputs / "joined001_fort.23"
    # file header, then detector header and data of each detector
    joined_path.write_bytes(b"".join(xz_records[:3] + xy_records[1:3]))

    xz_alone = fromfile(str(mock_outputs / "minimal001_fort.21")).pages[0]
    xy_alone = fromfile(str(mock_outputs / "minimal001_fort.22")).pages[0]
    joined = fromfile(str(joined_path))

    assert len(joined.pages) == 2
    for joined_page, page_alone in zip(joined.pages, (xz_alone, xy_alone)):
        assert joined_page.title == page_alone.title
        assert joined_page.data.shape == page_alone.data.shape
        np.testing.assert_array_equal(joined_page.data, page_alone.data)
        for axis_id in (AxisId.x, AxisId.y, AxisId.z):
            assert joined_page.axis(axis_id) == page_alone.axis(axis_id)

    assert joined.pages[0].data.shape[:3] == (4, 1, 4)
    assert joined.pages[1].data.shape[:3] == (4, 4, 1)


def test_detectors_with_different_number_of_bins(mock_outputs: Path):
    """Second detector cut to 4 x 2 x 1 bins, both pages must still be readable"""
    xz_records = read_records(mock_outputs / "minimal001_fort.21")
    xy_records = read_records(mock_outputs / "minimal001_fort.22")

    header = list(struct.unpack(DETECTOR_HEADER_FORMAT, xy_records[1][4:-4]))
    header[10] = 2  # ny
    header[9] = 0.0  # yhigh, y goes from -5 to 0 cm so the bin width stays 2.5 cm
    data = np.frombuffer(xy_records[2][4:-4], dtype=np.float32)[:8]
    cut_path = mock_outputs / "cut001_fort.24"
    cut_path.write_bytes(b"".join(xz_records[:3]) + make_record(struct.pack(DETECTOR_HEADER_FORMAT, *header)) +
                         make_record(data.tobytes()))

    estimator = fromfile(str(cut_path))

    assert estimator.pages[0].data.shape[:3] == (4, 1, 4)
    assert estimator.pages[1].data.shape[:3] == (4, 2, 1)
    np.testing.assert_array_equal(estimator.pages[1].data_raw, data.astype(np.float64) * 1000)  # GeV -> MeV


def test_single_detector_sets_estimator_mesh(mock_outputs: Path):
    """With one detector in the file the estimator has the same mesh as its page"""
    estimator = fromfile(str(mock_outputs / "minimal001_fort.21"))
    page = estimator.pages[0]

    assert estimator.x == page.x
    assert estimator.y == page.y
    assert estimator.z == page.z
    assert (estimator.x.n, estimator.y.n, estimator.z.n) == (4, 1, 4)


def test_data_block_to_array():
    """Same values as unpacking one float at a time, as float64 and writable"""
    values = np.random.default_rng(0).random(1000).astype(np.float32)
    data_block = values.tobytes()

    result = data_block_to_array(data_block)

    expected = np.array(struct.unpack(f"={values.size}f", data_block))
    np.testing.assert_array_equal(result, expected)
    assert result.dtype == np.float64
    assert result.flags.writeable
