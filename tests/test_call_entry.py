import os
import unittest
from pymchelper import bdo2txt


class TestCall(unittest.TestCase):
    def test_help(self):
        try:
            bdo2txt.main(["--help"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_version(self):
        try:
            bdo2txt.main(["--version"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_noarg(self):
        try:
            bdo2txt.main([])
        except SystemExit as e:
            self.assertEqual(e.code, 2)

    def test_many(self):
        bdo2txt.main(["--many", "tests/res/shieldhit/single/*.bdo", "--converter", "image"])
        files = os.listdir("tests/res/shieldhit/single")
        png_files = [f for f in files if f.endswith(".png")]
        bdo_files = [f for f in files if f.endswith(".bdo")]
        self.assertGreater(len(files), 4)
        self.assertEqual(len(png_files), len(bdo_files))


if __name__ == '__main__':
    unittest.main()
