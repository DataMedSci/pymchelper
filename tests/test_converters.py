"""
Tests for converters (so far only pld2sobp.py)
"""
import unittest
import logging
import pymchelper.utils.pld2sobp

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

if __name__ == '__main__':
    unittest.main()
