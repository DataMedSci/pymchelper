import logging
import shutil
import sys
from pathlib import Path
from typing import Generator, Tuple

import pytest

from pymchelper.executor.options import SimulationSettings
from pymchelper.executor.runner import Runner, SimulatorType

logger = logging.getLogger(__name__)

@pytest.fixture
def shieldhit_path() -> Generator[Path, None, None]:
    """Return SHIELD-HIT12A executable path"""
    yield Path("tests") / "res" / "mocks" / "shieldhit_minimal" / "shieldhit"
   
@pytest.fixture
def topas_path() -> Generator[Tuple[Path, Path], None, None]:
    """Return topas executable and input file paths"""
    topas_exec_path = Path("tests") / "res" / "mocks" / "topas_minimal" / "topas"
    topas_input_path = Path("tests") / "res" / "mocks" / "topas_minimal" / "minimal.txt"

    return topas_exec_path, topas_input_path


@pytest.mark.smoke
@pytest.mark.skipif(sys.platform == "darwin", reason="we don't have SHIELD-HIT12A demo binary for MacOSX")
@pytest.mark.skipif(sys.platform == "win32", reason="simulator mocks don't work on Windows")
def test_shieldhit(shieldhit_path: Path, tmp_path: Path):
    """TODO"""
    settings = SimulationSettings(input_path=str(shieldhit_path),
                                    simulator_type=SimulatorType.shieldhit,
                                    simulator_exec_path=str(shieldhit_path),
                                    cmdline_opts='-s')
    settings.set_no_of_primaries(10)
    logger.info(settings)

    r = Runner(settings=settings, jobs=2, output_directory=tmp_path)
    isRunOk = r.run()
    assert isRunOk

    data = r.get_data()
    logger.info(data)
    assert data is not None
    assert 'fluence' in data
    assert 'mesh' in data
    shutil.rmtree(tmp_path)

@pytest.mark.smoke
@pytest.mark.skipif(sys.platform == "darwin", reason="we don't have SHIELD-HIT12A demo binary for MacOSX")
@pytest.mark.skipif(sys.platform == "win32", reason="simulator mocks don't work on Windows")
def test_topas(topas_path: Path, tmp_path: Path):
    """TODO"""
    topas_exec_path, topas_input_path = topas_path

    settings = SimulationSettings(input_path=str(topas_input_path),
                                    simulator_type=SimulatorType.topas,
                                    simulator_exec_path=str(topas_exec_path))
    logger.info(settings)

    r = Runner(settings=settings, jobs=2, output_directory=tmp_path)
    
    isRunOk = r.run()
    assert isRunOk
    
    #ensure that correct number of threads is set in the input file
    with open(r.settings.input_path, "r") as input_file:
        contents = input_file.read()
        assert "i:Ts/NumberOfThreads = 0" not in contents
        assert "i:Ts/NumberOfThreads = 2" in contents
        
    data = r.get_data()
    logger.info(data)
    assert data is not None
    assert 'fluence_bp_protons_xy' in data
    assert 'fluence_bp_protons_xy2' in data
    
    shutil.rmtree(tmp_path)