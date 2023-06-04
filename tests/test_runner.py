import logging
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from pymchelper.executor.options import SimulationSettings
from pymchelper.executor.runner import Runner

logger = logging.getLogger(__name__)


@pytest.mark.smoke
@pytest.mark.skipif(sys.platform == "darwin", reason="we don't have SHIELD-HIT12A demo binary for MacOSX")
class TestRunner(unittest.TestCase):
    """
    TODO
    """

    def setUp(self):
        """
        TODO
        """
        self.sh_exec_path = Path("tests") / "res" / "mocks" / "shieldhit_minimal" / "shieldhit"
        self.sh_input_cfg = {
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
        self.topas_exec_path = Path("tests") / "res" / "mocks" / "topas_minimal" / "topas"
        self.topas_input_cfg = {
            'minimal.txt': """# GENERAL
i:Ts/ShowHistoryCountAtInterval = 2
i:Ts/NumberOfThreads = 0
b:Ts/ShowCPUTime = "True"
i:Ts/Seed = 1

# GEOMETRY

s:Ge/World/Type     = "TsCylinder"
s:Ge/World/Material = "Vacuum"
d:Ge/World/Rmax = 5 cm
d:Ge/World/HL = 3 cm
d:Ge/World/TransZ =  Ge/World/HL cm

s:Ge/PhantomScoringCoarseXY/Type     = "TsBox"
s:Ge/PhantomScoringCoarseXY/Parent = "World"
d:Ge/PhantomScoringCoarseXY/HLX = 1.5 cm
d:Ge/PhantomScoringCoarseXY/HLY = 1.5 cm
d:Ge/PhantomScoringCoarseXY/HLZ = 8.75 mm
d:Ge/PhantomScoringCoarseXY/TransZ = 0. mm
i:Ge/PhantomScoringCoarseXY/ZBins    = 1
i:Ge/PhantomScoringCoarseXY/XBins    = 4
i:Ge/PhantomScoringCoarseXY/YBins    = 4
b:Ge/PhantomScoringCoarseXY/IsParallel = "True"

s:Ge/PhantomScoringCoarseXY2/Type     = "TsBox"
s:Ge/PhantomScoringCoarseXY2/Parent = "World"
d:Ge/PhantomScoringCoarseXY2/HLX = 1.5 cm
d:Ge/PhantomScoringCoarseXY2/HLY = 1.5 cm
d:Ge/PhantomScoringCoarseXY2/HLZ = 8.75 mm
d:Ge/PhantomScoringCoarseXY2/TransX = 1.5 mm
d:Ge/PhantomScoringCoarseXY2/TransY = 1.5 mm
i:Ge/PhantomScoringCoarseXY2/ZBins    = 1
i:Ge/PhantomScoringCoarseXY2/XBins    = 4
i:Ge/PhantomScoringCoarseXY2/YBins    = 4
b:Ge/PhantomScoringCoarseXY2/IsParallel = "True"

# PARTICLE SOURCE
s:Ge/BeamPosition/Parent="World"
d:Ge/BeamPosition/TransZ = -11 cm
d:Ge/BeamPosition/RotX=0. deg

s:So/Demo/Type = "Beam"
s:So/Demo/BeamParticle = "proton"
s:So/Demo/Component = "BeamPosition"
d:So/Demo/BeamEnergy = 60 MeV
u:So/Demo/BeamEnergySpread = 1
s:So/Demo/BeamPositionDistribution = "Flat"
s:So/Demo/BeamPositionCutoffShape = "Ellipse" # Rectangle or Ellipse (if Flat or Gaussian)
d:So/Demo/BeamPositionCutoffX = 2. cm # X extent of position (if Flat or Gaussian)
d:So/Demo/BeamPositionCutoffY = 2. cm # Y extent of position (if Flat or Gaussian)
s:So/Demo/BeamAngularDistribution = "None"
i:So/Demo/NumberOfHistoriesInRun = Ts/ShowHistoryCountAtInterval * 10

s:Sc/FluenceBPprotonsXY/Quantity                  = "Fluence"
s:Sc/FluenceBPprotonsXY/WeightBy                  = "Track"
s:Sc/FluenceBPprotonsXY/Component                 = "PhantomScoringCoarseXY"
sv:Sc/FluenceBPprotonsXY/Report = 2 "Mean" "Standard_Deviation"
s:Sc/FluenceBPprotonsXY/IfOutputFileAlreadyExists = "Overwrite"
s:Sc/FluenceBPprotonsXY/OutputFile = "fluence_bp_protons_xy"
sv:Sc/FluenceBPprotonsXY/OnlyIncludeIfIncidentParticlesNamed = 1 "proton"

s:Sc/FluenceBPprotonsXY2/Quantity                  = "Fluence"
s:Sc/FluenceBPprotonsXY2/WeightBy                  = "Track"
s:Sc/FluenceBPprotonsXY2/Component                 = "PhantomScoringCoarseXY2"
sv:Sc/FluenceBPprotonsXY2/Report = 2 "Mean" "Standard_Deviation"
s:Sc/FluenceBPprotonsXY2/IfOutputFileAlreadyExists = "Overwrite"
s:Sc/FluenceBPprotonsXY2/OutputFile = "fluence_bp_protons_xy2"
sv:Sc/FluenceBPprotonsXY2/OnlyIncludeIfIncidentParticlesNamed = 1 "proton"
"""}

    def test_shieldhit(self):
        """
        TODO
        """
        dirpath = tempfile.mkdtemp()

        for config_file in self.sh_input_cfg:
            print(config_file)
            file_path = Path(dirpath) / config_file
            with open(file_path, 'w') as output_file:
                output_file.write(self.sh_input_cfg[config_file])

        settings = SimulationSettings(input_path=dirpath,
                                      simulator_type='shieldhit',
                                      simulator_exec_path=self.sh_exec_path,
                                      cmdline_opts='-s')
        settings.set_no_of_primaries(10)

        r = Runner(jobs=2, output_directory=dirpath)
        isRunOk = r.run(settings=settings)
        self.assertTrue(isRunOk)

        data = r.get_data()
        self.assertIsNotNone(data)
        shutil.rmtree(dirpath)

        # logger.info(data)

    def test_topas(self):
        """
        TODO
        """
        
        dirpath = tempfile.mkdtemp()

        for config_file in self.topas_input_cfg:
            print(config_file)
            file_path = Path(dirpath) / config_file
            with open(file_path, 'w') as output_file:
                output_file.write(self.topas_input_cfg[config_file])

        settings = SimulationSettings(input_path=dirpath,
                                        simulator_type='topas',
                                        simulator_exec_path=self.topas_exec_path,
                                        cmdline_opts='-s')

        r = Runner(jobs=2, output_directory=dirpath)
        isRunOk = r.run(settings=settings)
        self.assertTrue(isRunOk)

        data = r.get_data()
        self.assertIsNotNone(data)
        shutil.rmtree(dirpath)

        # logger.info(data)