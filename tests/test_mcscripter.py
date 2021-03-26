"""
Tests for mcscripter
"""
import logging
import os
import shutil
import tempfile
import unittest

import pytest

import pymchelper.utils.mcscripter

logger = logging.getLogger(__name__)


class TestMcScripter(unittest.TestCase):
    def setUp(self):
        # save location of current working directory
        self.local_wdir = os.getcwd()

    def tearDown(self):
        # it may happen that mcscripter has changed local working directory to something else
        # therefore we set it back to original value
        os.chdir(self.local_wdir)

    @pytest.mark.smoke
    def test_help(self):
        """ Print usage and exit normally.
        """
        try:
            pymchelper.utils.mcscripter.main(["--help"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    @pytest.mark.smoke
    def test_version(self):
        """ Print usage and exit normally.
        """
        try:
            pymchelper.utils.mcscripter.main(["--version"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_noarg(self):
        """ Call without args will cause it to fail.
        """
        try:
            pymchelper.utils.mcscripter.main([])
        except SystemExit as e:
            self.assertEqual(e.code, 2)

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_simple(self):
        """ Simple conversion including diagnostic output.
        """
        import os
        import sys
        inp_dir = os.path.join("tests", "res", "shieldhit", "mcscripter")
        inp_cfg = os.path.join(inp_dir, "test.cfg")
        out_dir = tempfile.mkdtemp()  # make temp working dir for output files
        try:
            pymchelper.utils.mcscripter.main([inp_cfg])
            self.assertTrue(os.path.isdir(out_dir))
            self.assertTrue(os.path.isdir(os.path.join(out_dir, "12C")))
            self.assertTrue(os.path.isdir(os.path.join(out_dir, "12C", "0333.100")))
            self.assertTrue(os.path.isfile(os.path.join(out_dir, "12C", "0333.100", "beam.dat")))
            self.assertTrue(os.path.islink(os.path.join(out_dir, "12C", "0333.100", "Water.txt")))
            logger.info("Removing directory {:s}".format(out_dir))
            shutil.rmtree(out_dir)
        except AttributeError:  # on Windows with Python os.symlink is not enabled
            self.assertEqual(os.name, 'nt')
            self.assertEqual(sys.version_info[0], 2)
            logger.info("Removing directory {:s}".format(out_dir))
            shutil.rmtree(out_dir)


if __name__ == '__main__':
    unittest.main()
