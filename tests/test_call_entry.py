import os
import unittest
import logging
from pymchelper import run
from examples import generate_detect_shieldhit, generate_fluka_input
from pymchelper.flair import Input

logger = logging.getLogger(__name__)


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
        run.main(["image", "--many", "tests/res/shieldhit/single/*.bdo"])
        files = os.listdir(os.path.join("tests", "res", "shieldhit", "single"))
        png_files = [f for f in files if f.endswith(".png")]
        bdo_files = [f for f in files if f.endswith(".bdo")]
        self.assertGreater(len(files), 4)
        self.assertEqual(len(png_files), len(bdo_files))

    def test_many_excel(self):
        run.main(["excel", "--many", "tests/res/shieldhit/single/*.bdo"])
        files = os.listdir(os.path.join("tests", "res", "shieldhit", "single"))
        xls_files = [f for f in files if f.endswith(".xls")]
        bdo_files = [f for f in files if f.endswith(".bdo")]
        self.assertGreater(len(files), 4)
        self.assertEqual(len(xls_files), len(bdo_files))

    def test_many_shield_nscale(self):
        run.main(["image", "--many", "tests/res/shieldhit/single/*.bdo", "-n", "100000000"])
        files = os.listdir(os.path.join("tests", "res", "shieldhit", "single"))
        png_files = [f for f in files if f.endswith(".png")]
        bdo_files = [f for f in files if f.endswith(".bdo")]
        self.assertGreater(len(files), 4)
        self.assertEqual(len(png_files), len(bdo_files))


class TestCallExample(unittest.TestCase):
    def test_shieldhit(self):
        generate_detect_shieldhit.main()
        expected_filename = "detect.dat"

        logger.info("checking presence of {:s} file".format(expected_filename))
        self.assertTrue(os.path.isfile(expected_filename))

    def test_fluka(self):
        generate_fluka_input.main()
        expected_filename = "fl_sim.inp"

        logger.info("checking presence of {:s} file".format(expected_filename))
        self.assertTrue(os.path.isfile(expected_filename))

        input = Input.Input()
        input.read(expected_filename)

        logger.info("checking presence of RANDOMIZ card")
        self.assertIn("RANDOMIZ", input.cards)

        logger.info("checking if there is only one RANDOMIZ card ")
        self.assertEqual(len(input.cards["RANDOMIZ"]), 1)

        logger.info("checking if RNG setting is correct ")
        self.assertEqual(input.cards["RANDOMIZ"][0].whats()[2], 137)

        logger.info("checking presence of USRBIN cards")
        self.assertIn("USRBIN", input.cards)

        logger.info("checking if there are 8 USRBIN cards")
        self.assertEqual(len(input.cards["USRBIN"]), 2 * 4)


if __name__ == '__main__':
    unittest.main()
