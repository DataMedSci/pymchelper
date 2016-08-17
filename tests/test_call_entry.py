import os
import unittest
from pymchelper import run
from examples import generate_detect_shieldhit


class TestCallMain(unittest.TestCase):
    def test_help(self):
        try:
            run.main(["--help"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_version(self):
        try:
            run.main(["--version"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_noarg(self):
        try:
            run.main([])
        except SystemExit as e:
            self.assertEqual(e.code, 2)

    def test_many_shield(self):
        run.main(["--many", "tests/res/shieldhit/single/*.bdo", "--converter", "image"])
        files = os.listdir("tests/res/shieldhit/single")
        png_files = [f for f in files if f.endswith(".png")]
        bdo_files = [f for f in files if f.endswith(".bdo")]
        self.assertGreater(len(files), 4)
        self.assertEqual(len(png_files), len(bdo_files))


class TestCallExample(unittest.TestCase):
    def test_help(self):
        generate_detect_shieldhit.main()
        self.assertTrue(os.path.isfile("detect.dat"))


if __name__ == '__main__':
    unittest.main()
