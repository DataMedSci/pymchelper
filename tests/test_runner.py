import logging
import sys
from pathlib import Path
from typing import Generator

import pytest

from pymchelper.executor.options import SimulationSettings
from pymchelper.executor.runner import Runner


@pytest.fixture(scope="module")
def example_input_cfg() -> Generator[dict, None, None]:
    """Return example input configuration for SHIELD-HIT12A"""
    input_cfg = {
        'beam.dat':
        """RNDSEED      	89736501     ! Random seed
JPART0       	2           ! Incident particle type
TMAX0           150.0   0.0  ! Incident energy; (MeV/nucl)
NSTAT           1000    -1 ! NSTAT, Step of saving
STRAGG          2            ! Straggling: 0-Off 1-Gauss, 2-Vavilov
MSCAT           2            ! Mult. scatt 0-Off 1-Gauss, 2-Moliere
NUCRE           0            ! Nucl.Reac. switcher: 1-ON, 0-OFF
        """,
        'mat.dat':
        """MEDIUM 1
ICRU 276
END
        """,
        'detect.dat':
        """
        Geometry Cyl
            Name MyCyl
            R  0.0  10.0    1
            Z  0.0  20.0    1000
        Output
            Filename data.bdo
            Geo MyCyl
            Quantity Dose
        """,
        'geo.dat':
        """*---><---><--------><------------------------------------------------>
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
    1 1000    0"""
    }
    yield input_cfg


@pytest.mark.smoke
@pytest.mark.skipif(sys.platform == "darwin", reason="we don't have SHIELD-HIT12A demo binary for MacOSX")
def test_runner(example_input_cfg: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, shieldhit_binary_path: Path,
                shieldhit_demo_binary_installed):
    """Test if single BDO file is converted to Excel file"""
    logging.info("Changing working directory to %s", tmp_path)
    monkeypatch.chdir(tmp_path)

    for config_file, file_content in example_input_cfg.items():
        file_path = tmp_path / config_file
        file_path.write_text(file_content)
        assert file_path.exists()
        assert file_path.is_file()
        assert file_path.stat().st_size > 0

    settings = SimulationSettings(input_path=tmp_path, simulator_exec_path=shieldhit_binary_path, cmdline_opts='-s')
    settings.set_no_of_primaries(10)

    r = Runner(jobs=2, output_directory=str(tmp_path))
    isRunOk = r.run(settings=settings)
    assert isRunOk

    data = r.get_data()
    assert data is not None
