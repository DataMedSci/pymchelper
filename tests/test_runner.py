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
@pytest.mark.skip(reason="requires SHIELD-HIT12A demo binary; download removed, see #884")
def test_shieldhit(example_input_cfg: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                   shieldhit_binary_path: Path):
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
    is_run_ok = r.run()
    assert is_run_ok

    data = r.get_data()
    assert data is not None
    assert 'data' in data


@pytest.mark.smoke
@pytest.mark.skip(reason="requires SHIELD-HIT12A demo binary; download removed, see #884")
def test_merging(example_input_cfg: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, shieldhit_binary_path: Path):
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
    assert len(data['data'].pages) == 3

    # check if we get expected density
    rho_page = data['data'].pages[2]
    assert rho_page.data.shape == (1, 1, 100, 1, 1)
    assert rho_page.data[0, 0, 0, 0, 0] == 1.0
    assert np.unique(rho_page.data).size == 1

    # check if we get expected kinetic energy
    ekin_page = data['data'].pages[1]
    assert ekin_page.data.shape == (1, 1, 100, 1, 1)
    assert ekin_page.data[0, 0, 0, 0, 0] > 145.0
    assert ekin_page.data[0, 0, 0, 0, 0] < 155.0

    data_first_bin_dose = data['data'].pages[0].data[0, 0, 0, 0, 0]

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

    # ensure that correct number of threads is set in the copy of the input file in the working directory
    input_copy = Path(r.workspace_manager.working_directories_abs_paths[0]) / topas_input_path.name
    contents = input_copy.read_text()
    assert "i:Ts/NumberOfThreads = 0" not in contents
    assert "i:Ts/NumberOfThreads = 2" in contents
    # and the input file of the user stays as it was
    assert "i:Ts/NumberOfThreads = 2" not in topas_input_path.read_text()

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
                [0., 1.46468, 1.69978, 0.],
                [0.9081, 0., 0., 0.],
                [0, 0., 0., 0.]
            ]
        },
        "22": {
            "shape": [4, 4, 1],
            "4x4": [
                [0.4757, 0., 0., 0.],
                [0., 1.88021, 1.66488, 0.],
                [0., 1.0242, 1.05254, 0.],
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


def make_mock_simulator(path: Path, script: str) -> Path:
    """Write an executable shell script, used as a mock MC simulator"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n" + script)
    path.chmod(0o755)
    return path


def make_shieldhit_input(directory: Path) -> Path:
    """Directory with the four input files SHIELD-HIT12A needs, content doesn't matter for the mocks"""
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ("beam.dat", "detect.dat", "geo.dat", "mat.dat"):
        (directory / filename).write_text("x\n")
    return directory


def run_shieldhit_mock(tmp_path: Path,
                       executable: Path,
                       jobs: int,
                       cmdline_opts: str = "",
                       keep_workspace_after_run: bool = False) -> Runner:
    """Run the mock with Runner, working directories in tmp_path/out"""
    settings = SimulationSettings(input_path=str(make_shieldhit_input(tmp_path / "input")),
                                  simulator_type=SimulatorType.shieldhit,
                                  simulator_exec_path=str(executable),
                                  cmdline_opts=cmdline_opts)
    runner = Runner(settings=settings,
                    jobs=jobs,
                    keep_workspace_after_run=keep_workspace_after_run,
                    output_directory=str(tmp_path / "out"))
    runner.run()
    return runner


@pytest.mark.skipif(sys.platform == "win32", reason="simulator mocks don't work on Windows")
@pytest.mark.parametrize("cmdline_opts, expected_seed_options", [
    ("-n 100", ["-N 1", "-N 2"]),
    ("-N 1000 -n 100", ["-N 1001", "-N 1002"]),
    ("--seedoffset 5000 -n 100", ["--seedoffset 5001", "--seedoffset 5002"]),
])
def test_shieldhit_seeds(cmdline_opts: str, expected_seed_options: list, tmp_path: Path):
    """Each job gets the seed given by the user plus its job number"""
    executable = make_mock_simulator(tmp_path / "bin" / "shieldhit", 'echo "$@" > arguments.txt\n')
    runner = run_shieldhit_mock(tmp_path, executable, jobs=2, cmdline_opts=cmdline_opts, keep_workspace_after_run=True)

    for working_dir, expected in zip(runner.workspace_manager.working_directories_abs_paths, expected_seed_options):
        arguments = (Path(working_dir) / "arguments.txt").read_text()
        assert expected in arguments
        assert arguments.count("-N") + arguments.count("--seedoffset") == 1


@pytest.mark.skipif(sys.platform == "win32", reason="simulator mocks don't work on Windows")
def test_get_data_reads_only_last_run(tmp_path: Path):
    """Working directories left by an earlier run with more jobs are not merged"""
    bdo_dir = Path(__file__).resolve().parent / "res" / "shieldhit" / "averaging"
    first = make_mock_simulator(tmp_path / "bin1" / "shieldhit",
                                f'cp "{bdo_dir}/normalisation-5_aggregation-mean_0001.bdo" dose.bdo\n')
    second = make_mock_simulator(tmp_path / "bin2" / "shieldhit",
                                 f'cp "{bdo_dir}/normalisation-5_aggregation-mean_0002.bdo" dose.bdo\n')
    run_shieldhit_mock(tmp_path, first, jobs=4, keep_workspace_after_run=True)
    runner = run_shieldhit_mock(tmp_path, second, jobs=2)

    estimator = runner.get_data()["dose"]
    expected = fromfile(str(bdo_dir / "normalisation-5_aggregation-mean_0002.bdo"))
    assert estimator.file_counter == 2
    assert estimator.pages[0].data_raw == pytest.approx(expected.pages[0].data_raw)


@pytest.mark.skipif(sys.platform == "win32", reason="simulator mocks don't work on Windows")
def test_simulator_error_is_shown(tmp_path: Path):
    """When the simulator fails, its output is in the error"""
    executable = make_mock_simulator(tmp_path / "bin" / "shieldhit",
                                     "echo \"ERROR: material 'Wter' not found\" >&2\nexit 2\n")
    with pytest.raises(RuntimeError, match="Wter"):
        run_shieldhit_mock(tmp_path, executable, jobs=2)


@pytest.mark.skipif(sys.platform == "win32", reason="simulator mocks don't work on Windows")
def test_executable_path_with_space(tmp_path: Path):
    """The executable path is one argument even with a space in it"""
    executable = make_mock_simulator(tmp_path / "my sims" / "shieldhit", "touch done.txt\n")
    runner = run_shieldhit_mock(tmp_path, executable, jobs=1, keep_workspace_after_run=True)

    assert (Path(runner.workspace_manager.working_directories_abs_paths[0]) / "done.txt").exists()


@pytest.mark.parametrize("randomiz_line, expected_seed", [
    ("RANDOMIZ          1.      777.\n", 777),
    ("RANDOMIZ          1.\n", 0),
    ("RANDOMIZ, 1., 777.\n", 777),
])
def test_fluka_user_seed(randomiz_line: str, expected_seed: int, tmp_path: Path):
    """WHAT(2) of the RANDOMIZ card is read in fixed and free format"""
    input_file = tmp_path / "input.inp"
    input_file.write_text("TITLE\nx\n" + randomiz_line + "START           100.\nSTOP\n")

    assert Runner._read_fluka_rng_seed(str(input_file)) == expected_seed


def test_fluka_randomiz_added_before_start(tmp_path: Path):
    """A missing RANDOMIZ card is added before START, where FLUKA still reads it"""
    input_file = tmp_path / "input.inp"
    input_file.write_text("TITLE\nno seed card\nSTART           100.\nSTOP\n")

    Runner._Runner__update_fluka_input_file(str(input_file), 2)

    lines = input_file.read_text().splitlines()
    assert lines[2].startswith("RANDOMIZ")
    assert lines[3].startswith("START")


def test_runmc_quiet_level(monkeypatch: pytest.MonkeyPatch):
    """-q, -qq and -qqq set WARNING, ERROR and CRITICAL"""
    from types import SimpleNamespace
    from pymchelper.utils.runmc import set_logger_level

    for quiet, expected in ((1, logging.WARNING), (2, logging.ERROR), (3, logging.CRITICAL)):
        root_logger = logging.getLogger()
        monkeypatch.setattr(root_logger, "handlers", [])
        set_logger_level(SimpleNamespace(quiet=quiet, verbose=0))
        assert root_logger.level == expected
