"""
Tests for converters (so far only pld2sobp.py)
"""
import unittest
import logging
import pymchelper.utils.mcscripter
import pymchelper.run

logger = logging.getLogger(__name__)


class TestMcScripter(unittest.TestCase):
    def test_help(self):
        """ Print usage and exit normally.
        """
        try:
            pymchelper.utils.mcscripter.main([])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_simple(self):
        """ Simple conversion including diagnostic output.
        """
        import os
        inp_dir = os.path.join("tests", "res", "shieldhit", "mcscripter")
        inp_cfg = os.path.join(inp_dir, "test.cfg")
        out_dir = "wdir"
        try:
            pymchelper.utils.mcscripter.main([inp_cfg])
        except SystemExit as e:
            self.assertEqual(e.code, 0)
        self.assertTrue(os.path.isdir(out_dir))
        self.assertTrue(os.path.isdir(os.path.join(out_dir, "12C")))
        self.assertTrue(os.path.isdir(os.path.join(out_dir, "12C", "0333.100")))
        self.assertTrue(os.path.isfile(os.path.join(out_dir, "12C", "0333.100", "beam.dat")))
        self.assertTrue(os.path.islink(os.path.join(out_dir, "12C", "0333.100", "Water.txt")))


if __name__ == '__main__':
    unittest.main()
