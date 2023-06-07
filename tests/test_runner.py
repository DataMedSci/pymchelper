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

@pytest.fixture
def shieldhit_path():
    return Path("tests") / "res" / "mocks" / "shieldhit_minimal" / "shieldhit"
   
@pytest.fixture
def topas_path():
    topas_exec_path = Path("tests") / "res" / "mocks" / "topas_minimal" / "topas"
    topas_input_path = Path("tests") / "res" / "mocks" / "topas_minimal" / "minimal.txt"

    return topas_exec_path, topas_input_path


@pytest.mark.smoke
@pytest.mark.skipif(sys.platform == "darwin", reason="we don't have SHIELD-HIT12A demo binary for MacOSX")
@pytest.mark.skipif(sys.platform == "win32", reason="simulator mocks don't work on Windows")
def test_shieldhit(shieldhit_path):
    """
    TODO
    """
    dirpath = tempfile.mkdtemp()

    settings = SimulationSettings(input_path=shieldhit_path,
                                    simulator_type=SimulatorType.shieldhit,
                                    simulator_exec_path=shieldhit_path,
                                    cmdline_opts='-s')
    settings.set_no_of_primaries(10)
    print(settings)

    r = Runner(settings=settings, jobs=2, output_directory=dirpath)
    isRunOk = r.run()
    assert isRunOk

    data = r.get_data()
    print(data)
    assert data is not None
    assert 'fluence' in data
    assert 'mesh' in data
    shutil.rmtree(dirpath)

    # logger.info(data)

@pytest.mark.smoke
@pytest.mark.skipif(sys.platform == "darwin", reason="we don't have SHIELD-HIT12A demo binary for MacOSX")
@pytest.mark.skipif(sys.platform == "win32", reason="simulator mocks don't work on Windows")
def test_topas(topas_path):
    """
    TODO
    """
    topas_exec_path, topas_input_path = topas_path
    
    dirpath = tempfile.mkdtemp()

    settings = SimulationSettings(input_path=topas_input_path,
                                    simulator_type=SimulatorType.topas,
                                    simulator_exec_path=topas_exec_path)
    print(settings)

    r = Runner(settings=settings, jobs=2, output_directory=dirpath)
    
    isRunOk = r.run()
    assert isRunOk

    data = r.get_data()
    print(data)
    assert data is not None
    shutil.rmtree(dirpath)

    # logger.info(data)