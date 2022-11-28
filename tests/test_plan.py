import os
import logging
import pytest
import unittest

from pathlib import Path

import pymchelper.utils.radiotherapy.plan

logger = logging.getLogger(__name__)


@pytest.mark.smoke
class TestPlanConverter(unittest.TestCase):
    path_bm = Path('tests', 'res', 'pld', 'beam_model_generic.csv')
    path_pld = Path('tests', 'res', 'pld', 'test.pld')
    path_dicom1 = Path('tests', 'res', 'dicom', 'RN.1.2.246.352.71.5.37402163639.162240.20220929101251.dcm')
    path_dicom2 = Path('tests', 'res', 'dicom', 'RN.1.2.246.352.71.5.361940808526.37240.20200311150225.dcm')

    def test_call_cmd_no_option(self):
        """Description needed."""
        with pytest.raises(SystemExit) as e:
            logger.info("Catching {:s}".format(str(e)))
            pymchelper.utils.radiotherapy.plan.main([])
            assert e.value == 2

    def test_call_cmd_option(self):
        """Description needed."""
        for option_name in ["version", "help"]:
            with pytest.raises(SystemExit) as e:
                logger.info("Catching {:s}".format(str(e)))
                pymchelper.utils.radiotherapy.plan.main(['--' + option_name])
                assert e.value == 0

    # def test_pld(self):
    #     """ Test PLD plan loading with and without beam model """
    #     with pytest.raises(SystemExit) as e:
    #         logger.info("Catching {:s}".format(str(e)))
    #         pymchelper.utils.radiotherapy.plan.main([str(self.path_pld)])
    #         assert e.value == 0
    #
    # def test_dicom(self):
    #     """ Test DICOM plan loading with and without beam model """
    #     with pytest.raises(SystemExit) as e:
    #         logger.info("Catching {:s}".format(str(e)))
    #         pymchelper.utils.radiotherapy.plan.main([str(self.path_dicom1)])
    #         assert e.value == 0

    # def test_pld(self):
    #     """ Test PLD file loading with and without beam model """
    #
    #     cfopts = [[str(self.path_pld)],
    #               [str(self.path_dicom1)],
    #               ['-b ' + str(self.path_bm) + ' ' + str(self.path_pld)],
    #               ['-b ' + str(self.path_bm) + ' ' + str(self.path_dicom1)]
    #               ]
    #
    #     for option_name in cfopts:
    #         with pytest.raises(SystemExit) as e:
    #             logger.info("Catching {:s}".format(str(e)))
    #             pymchelper.utils.radiotherapy.plan.main([option_name])
    #             assert e.value == 0


if __name__ == '__main__':
    unittest.main()
