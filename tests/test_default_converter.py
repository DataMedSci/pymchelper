import difflib
import filecmp
import os
import sys
import subprocess
import tempfile
import shutil
import unittest
import logging

import numpy as np

from pymchelper import run
from pymchelper.estimator import ErrorEstimate
from pymchelper.input_output import fromfilelist, fromfile

logger = logging.getLogger(__name__)


def shieldhit_binary():
    """
    :return: location of bdo2txt binary suitable for Linux or Windows
    """
    exe_path = os.path.join("tests", "res", "shieldhit", "converter", "bdo2txt")
    if os.name == 'nt':
        exe_path += ".exe"
    logger.debug("bdo2txt binary: " + exe_path)
    return exe_path


def run_bdo2txt_binary(inputfile, working_dir, bdo2txt_path, silent=True):
    logger.info("running: " + bdo2txt_path + " " + inputfile)
    with open(os.devnull, 'w') as shutup:
        if silent:
            retVal = subprocess.call(args=[bdo2txt_path, inputfile], stdout=shutup, stderr=shutup)
        else:
            retVal = subprocess.call(args=[bdo2txt_path, inputfile])
    return retVal


class TestErrorEstimate(unittest.TestCase):
    def test_normal_numbers(self):

        # several files for the same estimator, coming from runs with different RNG seed
        file_list = ["tests/res/shieldhit/generated/many/msh/aen_0_p000{:d}.bdo".format(i) for i in range(1, 4)]

        # read each of the files individually into estimator object
        estimator_list = [fromfile(file_path) for file_path in file_list]

        for error in ErrorEstimate:  # all possible error options (none, stddev, stderr)
            logger.info("Checking error calculation for error = {:s}".format(error.name))
            for nan in (False, True):  # include or not NaNs in averaging
                logger.info("Checking error calculation for nan option = {:s}".format(str(nan)))
                # read list of the files into one estimator object, doing averaging and error calculation
                merged_estimators = fromfilelist(file_list, error=error, nan=nan)

                # manually calculate mean and check if correct
                for page_no, page in enumerate(merged_estimators.pages):
                    mean_value = np.mean([estimator.pages[page_no].data_raw for estimator in estimator_list])
                    self.assertEqual(mean_value, merged_estimators.pages[page_no].data_raw)

                # manually calculate mean and check if correct
                if error == ErrorEstimate.none:
                    for page in merged_estimators.pages:
                        self.assertTrue(np.isnan(page.error_raw) or not np.any(page.error_raw))
                elif error == ErrorEstimate.stddev:
                    for page_no, page in enumerate(merged_estimators.pages):
                        error_value = np.std([estimator.pages[page_no].data_raw for estimator in estimator_list], ddof=1)
                        self.assertEqual(error_value, merged_estimators.pages[page_no].error_raw)
                elif error == ErrorEstimate.stderr:
                    for page_no, page in enumerate(merged_estimators.pages):
                        error_value = np.std([estimator.pages[page_no].data_raw for estimator in estimator_list], ddof=1)
                        error_value /= np.sqrt(len(estimator_list))
                        self.assertEqual(error_value, merged_estimators.pages[page_no].error_raw)
                else:
                    return


class TestDefaultConverter(unittest.TestCase):
    main_dir = os.path.join("tests", "res", "shieldhit", "generated")
    single_dir = os.path.join(main_dir, "single")
    many_dir = os.path.join(main_dir, "many")
    bdo2txt_binary = shieldhit_binary()

    def test_shieldhit_files(self):
        # skip tests on MacOSX, as there is no suitable bdo2txt converter available yet
        if sys.platform.endswith('arwin'):
            return

        # loop over all .bdo files in all subdirectories
        for root, dirs, filenames in os.walk(self.single_dir):
            for input_basename in filenames:
                logger.info("root: {:s}, file: {:s}".format(root, input_basename))

                inputfile_rel_path = os.path.join(root, input_basename)  # choose input file
                self.assertTrue(inputfile_rel_path.endswith(".bdo"))

                working_dir = tempfile.mkdtemp()  # make temp working dir for converter output files
                logger.info("Creating directory {:s}".format(working_dir))

                # generate output file with native SHIELD-HIT12A converter
                ret_value = run_bdo2txt_binary(inputfile_rel_path,
                                               working_dir=working_dir,
                                               bdo2txt_path=self.bdo2txt_binary)
                self.assertEqual(ret_value, 0)

                # assuming input name 1.bdo, output file will be called 1.txt
                shieldhit_output = inputfile_rel_path[:-3] + "txt"
                logger.info("Expecting file {:s} to be generated by SHIELD-HIT12A converter".format(shieldhit_output))
                self.assertTrue(os.path.exists(shieldhit_output))

                shutil.move(shieldhit_output, working_dir)
                shieldhit_output_moved = os.path.join(working_dir, os.path.basename(shieldhit_output))
                logger.info("New location of SH12A file: {:s}".format(shieldhit_output_moved))
                self.assertTrue(os.path.exists(shieldhit_output_moved))

                # generate output with pymchelper assuming .ref extension for output file
                pymchelper_output = os.path.join(working_dir, input_basename[:-3] + "ref.txt")
                logger.info("Expecting file {:s} to be generated by pymchelper converter".format(pymchelper_output))
                run.main(["txt", inputfile_rel_path, pymchelper_output, '--error', 'none'])
                self.assertTrue(os.path.exists(pymchelper_output))

                # compare both files
                comparison = filecmp.cmp(shieldhit_output_moved, pymchelper_output)
                if not comparison:
                    with open(shieldhit_output_moved, 'r') as f1, open(pymchelper_output, 'r') as f2:
                        diff = difflib.unified_diff(f1.readlines(), f2.readlines())
                        diffs_to_print = list(next(diff) for _ in range(30))
                        for item in diffs_to_print:
                            logger.info(item)
                self.assertTrue(comparison)

                logger.info("Removing directory {:s}".format(working_dir))
                shutil.rmtree(working_dir)


if __name__ == '__main__':
    unittest.main()
