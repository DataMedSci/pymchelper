import logging
import os
import shutil
import sys
import tempfile
import unittest

import pytest

from pymchelper.executor.options import MCOptions
from pymchelper.executor.runner import Runner

logger = logging.getLogger(__name__)


@pytest.mark.smoke
class TestSHRunner(unittest.TestCase):

    def setUp(self):
        self.exec_path = os.path.join("tests", "res", "shieldhit", "executable", "shieldhit")
        if sys.platform == 'win32':
            self.exec_path += '.exe'
        print(self.exec_path)

    def test_simple(self):
        input_cfg = {
            'beam.dat': """RNDSEED      	89736501     ! Random seed
JPART0       	2           ! Incident particle type
TMAX0           150.0   0.0  ! Incident energy; (MeV/nucl)
NSTAT           1000    -1 ! NSTAT, Step of saving
STRAGG          2            ! Straggling: 0-Off 1-Gauss, 2-Vavilov
MSCAT           2            ! Mult. scatt 0-Off 1-Gauss, 2-Moliere
NUCRE           0            ! Nucl.Reac. switcher: 1-ON, 0-OFF
        """,
            'mat.dat': """MEDIUM 1
ICRU 276
END
        """,
            'detect.dat': """
        Geometry Cyl
            Name MyCyl
            R  0.0  10.0    1
            Z  0.0  20.0    1000
        Output
            Filename data.bdo
            Geo MyCyl
            Quantity Dose
        """,
            'geo.dat': """*---><---><--------><------------------------------------------------>
    0    0           protons, H2O 30 cm cylinder, r=10
*---><---><--------><--------><--------><--------><--------><-------->
  RCC    1       0.0       0.0       0.0       0.0       0.0      30.0
                10.0
  RCC    2       0.0       0.0      -5.0       0.0       0.0      35.0
                15.0
  RCC    3       0.0       0.0     -10.0       0.0       0.0      40.0
                20.0
  END
  001          +1
  002          +2     -1
  003          +3     -2
  END
    1    2    3
    1 1000    0"""}

        dirpath = tempfile.mkdtemp()

        for config_file in input_cfg:
            file_path = os.path.join(dirpath, config_file)
            with open(file_path, 'w') as output_file:
                output_file.write(input_cfg[config_file])

        opt = MCOptions(input_path=dirpath,
                        executable_path=self.exec_path,
                        user_opt='-s')
        opt.set_no_of_primaries(10)

        r = Runner(jobs=2, options=opt)
        workspaces = r.run(outdir=dirpath)
        self.assertIsNotNone(workspaces)

        data = r.get_data(dirpath)
        self.assertIsNotNone(data)
        shutil.rmtree(dirpath)

        # logger.info(data)
