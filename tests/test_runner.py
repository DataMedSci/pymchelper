import logging
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from pymchelper.executor.options import SimulationSettings
from pymchelper.executor.runner import Runner, SimulatorType

logger = logging.getLogger(__name__)


@pytest.mark.smoke
@pytest.mark.skipif(sys.platform == "darwin", reason="we don't have SHIELD-HIT12A demo binary for MacOSX")
@pytest.mark.skipif(sys.platform == "win32", reason="simulator mocks don't work on Windows")
class TestRunner(unittest.TestCase):
    """
    Test if runner runs mock simulators
    """

    def setUp(self):
        """
        TODO
        """
        self.sh_exec_path = Path("tests") / "res" / "mocks" / "shieldhit_minimal" / "shieldhit"
        self.topas_exec_path = Path("tests") / "res" / "mocks" / "topas_minimal" / "topas"
        self.topas_input_path = Path("tests") / "res" / "mocks" / "topas_minimal" / "minimal.txt"
        
    def test_shieldhit(self):
        """
        TODO
        """
        dirpath = tempfile.mkdtemp()

        settings = SimulationSettings(input_path=self.sh_exec_path,
                                      simulator_type=SimulatorType.shieldhit,
                                      simulator_exec_path=self.sh_exec_path,
                                      cmdline_opts='-s')
        settings.set_no_of_primaries(10)
        print(settings)

        r = Runner(settings=settings, jobs=2, output_directory=dirpath)
        isRunOk = r.run()
        self.assertTrue(isRunOk)

        data = r.get_data()
        print(data)
        self.assertIsNotNone(data)
        self.assertTrue('fluence' in data)
        self.assertTrue('mesh' in data)
        shutil.rmtree(dirpath)

        # logger.info(data)

    def test_topas(self):
        """
        TODO
        """
        
        dirpath = tempfile.mkdtemp()

        settings = SimulationSettings(input_path=self.topas_input_path,
                                        simulator_type=SimulatorType.topas,
                                        simulator_exec_path=self.topas_exec_path)
        print(settings)

        r = Runner(settings=settings, jobs=2, output_directory=dirpath)
        
        isRunOk = r.run()
        self.assertTrue(isRunOk)

        data = r.get_data()
        print(data)
        self.assertIsNotNone(data)
        shutil.rmtree(dirpath)

        # logger.info(data)