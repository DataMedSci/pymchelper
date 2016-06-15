import unittest
from pymchelper import bdo2txt


class TestFunMethod(unittest.TestCase):
    def test_check(self):
        self.assertRaises(SystemExit, bdo2txt.main, ["--help"])

if __name__ == '__main__':
    unittest.main()
