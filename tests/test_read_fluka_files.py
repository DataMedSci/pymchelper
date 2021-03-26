import os
import unittest
import logging

import pytest

import pymchelper.flair.Input as Input

logger = logging.getLogger(__name__)


class TestDefaultConverter(unittest.TestCase):
    main_dir = os.path.join("tests", "res", "fluka")
    generated_dir = os.path.join(main_dir, "generated")

    def check_directory(self, dir_path):
        for filename in os.listdir(self.main_dir):
            rel_path = os.path.join(self.main_dir, filename)
            if rel_path.endswith(".inp"):
                logger.info("opening " + rel_path)
                input = Input.Input()
                input.read(rel_path)

                logger.info("checking if START setting is correct ")
                self.assertGreater(int(input.cards["START"][0].whats()[1]), 100.0)

                logger.info("checking if BEAM setting is correct ")
                self.assertEqual(input.cards["BEAM"][0].sdum(), 'PROTON')

                logger.info("checking if more than one USRBIN present")
                self.assertGreater(len(input.cards["USRBIN"]), 1)

    @pytest.mark.smoke
    def test_load_input(self):
        self.check_directory(self.main_dir)
        self.check_directory(self.generated_dir)


if __name__ == '__main__':
    unittest.main()
