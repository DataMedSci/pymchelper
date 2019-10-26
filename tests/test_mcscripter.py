"""
Tests for mcscripter
"""
import unittest
import logging
import pymchelper.utils.mcscripter

logger = logging.getLogger(__name__)


class TestMcScripter(unittest.TestCase):
    def test_help(self):
        """ Print usage and exit normally.
        """
        try:
            pymchelper.utils.mcscripter.main(["--help"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

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

    def test_simple(self):
        """ Simple conversion including diagnostic output.
        """
        import os
        import sys
        inp_dir = os.path.join("tests", "res", "shieldhit", "mcscripter")
        inp_cfg = os.path.join(inp_dir, "test.cfg")
        out_dir = "wdir"
        try:
            pymchelper.utils.mcscripter.main([inp_cfg])
        except AttributeError:  # on Windows with Python os.symlink is not enabled
            self.assertEqual(os.name, 'nt')
            self.assertEqual(sys.version_info[0], 2)
        except SystemExit as e:
            self.assertEqual(e.code, 0)
            self.assertTrue(os.path.isdir(out_dir))
            self.assertTrue(os.path.isdir(os.path.join(out_dir, "12C")))
            self.assertTrue(os.path.isdir(os.path.join(out_dir, "12C", "0333.100")))
            self.assertTrue(os.path.isfile(os.path.join(out_dir, "12C", "0333.100", "beam.dat")))
            self.assertTrue(os.path.islink(os.path.join(out_dir, "12C", "0333.100", "Water.txt")))


if __name__ == '__main__':
    unittest.main()
