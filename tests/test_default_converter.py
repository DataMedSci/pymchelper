import os
import subprocess
import unittest
import logging

logger = logging.getLogger(__name__)


def shieldhit_binary():
    exe_path = os.path.join("tests", "res", "shieldhit", "converter", "bdo2txt")
    if os.name == 'nt':
        exe_path.append(".exe")
    logger.debug("bdo2txt binary: " + exe_path)
    return exe_path


def run_bdo2txt_binary(inputfile, working_dir, bdo2txt_path):
    with open(os.devnull, 'w') as shutup:
        logger.info("running" + bdo2txt_path + " " + inputfile)
        retVal = subprocess.call(args=[bdo2txt_path, inputfile], stdout=shutup, stderr=shutup)
    # retVal = subprocess.call(args=[bdo2txt_path, inputfile])
    return retVal


class TestDefaultConverter(unittest.TestCase):
    main_dir = os.path.join("tests", "res", "shieldhit", "generated")
    single_dir = os.path.join(main_dir, "single")
    many_dir = os.path.join(main_dir, "many")
    bdo2txt_binary = shieldhit_binary()

    def test_foo(self):
        for root, dirs, filenames in os.walk(self.single_dir):
            for f in filenames:
                logger.info("root: {:s}, file: {:s}".format(root, f))
                inputfile = os.path.join(root, f)
                ret_value = run_bdo2txt_binary(inputfile, working_dir=".", bdo2txt_path=self.bdo2txt_binary)
                self.assertEqual(ret_value, 0)


if __name__ == '__main__':
    unittest.main()
