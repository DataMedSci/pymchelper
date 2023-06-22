"""
Tests for converters
"""
import logging
from pathlib import Path
import shutil
import sys

import numpy as np
import pytest

from pymchelper import run
from pymchelper.input_output import fromfile
from tests.utils.types import YieldFixture

logger = logging.getLogger(__name__)


@pytest.mark.smoke
class TestTrip2Ddd:

    def test_help(self):
        """Print help text and exit normally."""
        try:
            run.main(["tripddd", "--help"])
        except SystemExit as e:
            assert not e.code

    def test_version(self):
        """Print version and exit normally."""
        try:
            run.main(["tripddd", "--version"])
        except SystemExit as e:
            assert not e.code

    def test_noarg(self):
        """If pymchelper is called without arguments it should fail."""
        try:
            run.main(["tripddd"])
        except SystemExit as e:
            assert 2 == e.code


def unpack_sparse_file(filename):
    logger.info("Unpacking sparse file %s", filename)
    npzfile = np.load(filename)
    data = npzfile['data']
    indices = npzfile['indices']
    shape = npzfile['shape']

    result = np.zeros(shape)
    for ind, dat in zip(indices, data):
        result[tuple(ind)] = dat
    return result


@pytest.fixture
def shieldhit_files() -> YieldFixture[Path]:
    single_dir = Path(__file__).parent / "res" / "shieldhit" / "generated" / "single"
    assert single_dir.exists()
    yield single_dir


@pytest.mark.skipif(sys.platform == "darwin", reason="MacOSX does not have bdo2txt converter")
def test_shieldhit_files(shieldhit_files: Path, tmp_path_factory: pytest.TempPathFactory):
    # loop over all .bdo files in all subdirectories
    for bdo_file_path in list(shieldhit_files.glob("**/*.bdo")):
        # make temp working dir for converter output files
        working_dir = tmp_path_factory.mktemp("single", True)

        # generate output with pymchelper assuming .ref extension for output file
        pymchelper_output = working_dir / (bdo_file_path.name[:-3] + "npz")
        run.main(["sparse", str(bdo_file_path), str(pymchelper_output)])
        assert pymchelper_output.exists()

        # read the original file into a estimator structure
        estimator_data = fromfile(str(bdo_file_path))
        assert np.any(estimator_data.pages[0].data)

        # unpack saved sparse matrix
        reconstructed_sparse_mtx = unpack_sparse_file(pymchelper_output)

        # check if unpacked shape is correct
        assert estimator_data.x.n == reconstructed_sparse_mtx.shape[0]
        assert estimator_data.y.n == reconstructed_sparse_mtx.shape[1]
        assert estimator_data.z.n == reconstructed_sparse_mtx.shape[2]

        # check if unpacked data is correct
        assert np.array_equal(estimator_data.pages[0].data, reconstructed_sparse_mtx)

        logger.info("Removing directory %s", working_dir)
        shutil.rmtree(working_dir)
