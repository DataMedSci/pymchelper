"""
Tests for converters (so far only pld2sobp.py)
"""
import unittest
import logging
import pymchelper.utils.pld2sobp
import pymchelper.run

logger = logging.getLogger(__name__)


class TestPld2Sobp(unittest.TestCase):
    def test_help(self):
        try:
            pymchelper.utils.pld2sobp.main(["--help"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_version(self):
        try:
            pymchelper.utils.pld2sobp.main(["--version"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_noarg(self):
        try:
            pymchelper.utils.pld2sobp.main([])
        except SystemExit as e:
            self.assertEqual(e.code, 2)

    def test_simple(self):
        import os
        inp_path = os.path.join("tests", "res", "pld", "test.pld")
        out_path = os.path.join("tests", "res", "pld", "test.dat")
        try:
            pymchelper.utils.pld2sobp.main(["-d", inp_path, out_path])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

        self.assertTrue(os.path.isfile(out_path))


class TestTrip2Ddd(unittest.TestCase):
    def test_help(self):
        try:
            pymchelper.run.main(["tripddd", "--help"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_version(self):
        try:
            pymchelper.run.main(["tripddd", "--version"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_noarg(self):
        try:
            pymchelper.run.main(["tripddd"])
        except SystemExit as e:
            self.assertEqual(e.code, 2)


if __name__ == '__main__':
    unittest.main()
