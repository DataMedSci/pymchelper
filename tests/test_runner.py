import logging
import sys
from pathlib import Path
from typing import Dict, Generator, Tuple
import numpy as np

import pytest
from pymchelper.estimator import Estimator

from pymchelper.input_output import fromfile
from pymchelper.executor.options import SimulationSettings
from pymchelper.executor.runner import Runner
from pymchelper.simulator_type import SimulatorType


@pytest.fixture
def topas_mock_path() -> Generator[Path, None, None]:
    """path to TOPAS mock executable"""
    main_dir = Path(__file__).resolve().parent
    yield main_dir / 'res' / 'mocks' / 'topas_minimal' / 'topas'


@pytest.fixture
def topas_input_path() -> Generator[Path, None, None]:
    """path to TOPAS input file"""
    main_dir = Path(__file__).resolve().parent
    yield main_dir / 'res' / 'mocks' / 'topas_minimal' / 'minimal.txt'


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
            Z  0.0  20.0    100
        Filter
            Name Primaries
            A = 1
            Z = 1
            GEN = 0
        Output
            Filename data.bdo
            Geo MyCyl
            Quantity Dose
            Quantity AvgEnergy Primaries
            Quantity Rho
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
def test_shieldhit(example_input_cfg: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, shieldhit_binary_path: Path,
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

    r = Runner(jobs=2, settings=settings, output_directory=str(tmp_path))
    isRunOk = r.run()
    assert isRunOk

    data = r.get_data()
    assert data is not None
    assert 'data_' in data


@pytest.mark.smoke
@pytest.mark.skipif(sys.platform == "darwin", reason="we don't have SHIELD-HIT12A demo binary for MacOSX")
def test_merging(example_input_cfg: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, shieldhit_binary_path: Path,
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

    settings = SimulationSettings(input_path=tmp_path,
                                  simulator_exec_path=shieldhit_binary_path,
                                  cmdline_opts='--silent')
    settings.set_no_of_primaries(500)

    r = Runner(jobs=3, settings=settings, output_directory=str(tmp_path), keep_workspace_after_run=True)
    isRunOk = r.run()
    assert isRunOk

    data = r.get_data()
    assert data is not None
    assert len(data['data_'].pages) == 3

    # check if we get expected density
    rho_page = data['data_'].pages[2]
    assert rho_page.data.shape == (1, 1, 100, 1, 1)
    assert rho_page.data[0, 0, 0, 0, 0] == 1.0
    assert np.unique(rho_page.data).size == 1

    # check if we get expected kinetic energy
    ekin_page = data['data_'].pages[1]
    assert ekin_page.data.shape == (1, 1, 100, 1, 1)
    assert ekin_page.data[0, 0, 0, 0, 0] > 145.0
    assert ekin_page.data[0, 0, 0, 0, 0] < 155.0

    data_first_bin_dose = data['data_'].pages[0].data[0, 0, 0, 0, 0]

    bdo_files = list(tmp_path.glob('run_*/data*.bdo'))
    assert len(bdo_files) == 3
    for bdo_file in bdo_files:
        assert bdo_file.exists()
        assert bdo_file.is_file()
        assert bdo_file.stat().st_size > 0
        bdo_data = fromfile(str(bdo_file))
        assert bdo_data is not None
        assert len(bdo_data.pages) == 3
        first_bin_dose = bdo_data.pages[0].data[0, 0, 0, 0, 0]
        # demo version of SHIELD-HIT12A cannot use different random seeds for each run,
        # therefore the first bin dose should be the same for all runs
        assert first_bin_dose == data_first_bin_dose


@pytest.mark.smoke
@pytest.mark.skipif(sys.platform == "darwin", reason="we don't have TOPAS binary for MacOSX")
@pytest.mark.skipif(sys.platform == "win32", reason="simulator mocks don't work on Windows")
def test_topas(topas_mock_path: Path, topas_input_path: Path, tmp_path: Path):
    """Test if runner can run TOPAS mock and read the output"""
    settings = SimulationSettings(input_path=str(topas_input_path),
                                  simulator_exec_path=str(topas_mock_path))
    logging.info(settings)

    r = Runner(settings=settings, jobs=2, output_directory=tmp_path)

    isRunOk = r.run()
    assert isRunOk

    # ensure that correct number of threads is set in the input file
    with open(r.settings.input_path, "r") as input_file:
        contents = input_file.read()
        assert "i:Ts/NumberOfThreads = 0" not in contents
        assert "i:Ts/NumberOfThreads = 2" in contents

    data = r.get_data()
    logging.info(data)
    assert data is not None
    assert 'fluence_bp_protons_xy' in data
    assert 'fluence_bp_protons_xy2' in data


@pytest.fixture
def fluka_expected_results() -> Generator[Dict[str, dict], None, None]:
    """Return expected result"""
    yield {
        "21": {
            "shape": [4, 1, 4],
            "4x4": [
                [0., 0., 0., 0.],
                [0., 0.00146468, 0.00169978, 0.],
                [0.00090805, 0., 0., 0.],
                [0, 0., 0., 0.]
            ]
        },
        "22": {
            "shape": [4, 4, 1],
            "4x4": [
                [0.00047575, 0., 0., 0.],
                [0., 0.00188021, 0.00166488, 0.],
                [0., 0.0010242, 0.00105254, 0.],
                [0., 0., 0., 0.]
            ]
        }
    }


@pytest.fixture
def fluka_path() -> Generator[Tuple[Path, Path], None, None]:
    """Return path to rfluka executable and input file"""
    executable = Path("tests") / "res" / "mocks" / "fluka_minimal" / "rfluka"
    input_file = Path("tests") / "res" / "mocks" / "fluka_minimal" / "minimal.inp"

    yield executable, input_file


@pytest.mark.smoke
@pytest.mark.skipif(sys.platform == "win32", reason="simulator mocks don't work on Windows")
def test_fluka(fluka_path: Tuple[Path, Path], tmp_path: Path, fluka_expected_results: Dict[str, dict]):
    """Test fluka generator with previously generated rfluka mock"""
    fluka_exec_path, fluka_input_path = fluka_path

    settings = SimulationSettings(input_path=fluka_input_path,
                                  simulator_type=SimulatorType.fluka,
                                  simulator_exec_path=fluka_exec_path)
    print(settings)

    r = Runner(settings=settings, jobs=2, output_directory=str(tmp_path))

    isRunOk = r.run()
    assert isRunOk

    data = r.get_data()
    print(data, len(data))
    assert data is not None
    assert '21' in data
    assert '22' in data
    assert 'fluka_binary' == data['21'].file_format
    assert 'fluka_binary' == data['22'].file_format

    __verify_fluka_file(data["21"], fluka_expected_results["21"])
    __verify_fluka_file(data["22"], fluka_expected_results["22"])


def __verify_fluka_file(actual_result: Estimator, expected_result: dict) -> None:
    """Compares content of generated fluka file with expected values"""
    assert b'* Minimal fluka file with 20 particles, two results, 4x4 bins' == actual_result.title
    assert expected_result["shape"] == [actual_result.x.n, actual_result.y.n, actual_result.z.n]

    expected = list(np.around(np.array(expected_result["4x4"]).flatten(), 4))
    result = list(np.around(np.array(actual_result.pages[0].data).flatten(), 4))
    assert expected == result, "Fluka data does not match expected values"
