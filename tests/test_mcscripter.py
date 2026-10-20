"""Tests for mcscripter"""
import logging
import os
from pathlib import Path
import enum
from typing import List
import pymchelper.utils.mcscripter
import pytest

logger = logging.getLogger(__name__)


class Configs(enum.Enum):
    """Collection of test cases for mcscripter."""

    simple = Path('simple', 'simple.cfg')
    full = Path('full', 'config.cfg')
    simple_no_user_tables = Path('simple', 'no_user_tables.cfg')

    def __init__(self, cfg_path: Path):
        self.cfg_path = cfg_path

    @classmethod
    def list(cls) -> List[Path]:
        """List of long paths to config files for each test"""
        return list(map(lambda c: c.relpath, cls))

    @classmethod
    def names(cls):
        """List of short names for each test"""
        return list(map(lambda c: str(c.value), cls))

    @property
    def relpath(self) -> Path:
        """Relative path to the config file"""
        return Path("tests", "res", "shieldhit", "mcscripter", self.cfg_path)


@pytest.fixture(scope='module')
def default_config_path() -> Path:
    """Path to the default configuration used for testing."""
    return Configs.full.relpath


@pytest.mark.parametrize("option_name", ["version", "help"])
def test_call_cmd_option(option_name: str):
    """Description needed."""
    with pytest.raises(SystemExit) as e:
        logger.info("Catching %s", e)
        pymchelper.utils.mcscripter.main(['--' + option_name])
    assert e.value.args[0] == 0


def test_call_cmd_no_option():
    """Description needed."""
    with pytest.raises(SystemExit) as e:
        logger.info("Catching %s", e)
        pymchelper.utils.mcscripter.main([])
    assert e.value.args[0] == 2


@pytest.mark.parametrize("config_path", Configs.list(), ids=Configs.names())
def test_parsing_config(config_path: Path):
    """Description needed."""
    logger.warning(f"CWD {os.getcwd()}")
    config = pymchelper.utils.mcscripter.read_config(path=config_path)
    assert config is not None
    assert config.const_dict
    assert 'TDIR' in config.const_dict
    assert config.const_dict['TDIR'] == 'template'
    assert 'beam.dat' in config.const_dict['FILES']
    if config_path != Configs.simple_no_user_tables.relpath:
        assert config.table_dict
        assert '1H' in config.table_dict['NAME']


@pytest.mark.parametrize("config_path", Configs.list(), ids=Configs.names())
def test_reading_template(config_path: Path):
    """Description needed."""
    config = pymchelper.utils.mcscripter.read_config(path=config_path)
    assert config is not None
    template = pymchelper.utils.mcscripter.read_template(cfg=config)
    assert template
    assert template.files
    assert template.files[0].fname == 'beam.dat'
    assert template.files[0].symlink is False
    if config_path == Configs.full.relpath:
        assert len(template.files[0].lines) == 10


@pytest.mark.parametrize("config_path", Configs.list(), ids=Configs.names())
def test_writing_template(config_path: Path, tmp_path: Path):
    """Description needed."""
    config = pymchelper.utils.mcscripter.read_config(path=config_path)
    assert config
    template = pymchelper.utils.mcscripter.read_template(cfg=config)
    assert template
    template.write(tmp_path, config)
    assert tmp_path.exists()
    assert Path(tmp_path, 'wdir', '1H').exists()
    if config_path == Configs.full.relpath:
        for current_dict in template.prepare(cfg=config):
            assert current_dict['E_'] >= 65.8
            assert current_dict['BSIGMA'] == '0.4'
        assert Path(tmp_path, 'wdir', '1H', '0246.000', 'beam.dat').exists()


@pytest.mark.parametrize("config_path", Configs.list(), ids=Configs.names())
def test_execution(config_path: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Description needed."""
    logger.debug(f"current working directory {os.getcwd()}")
    full_path_to_config = config_path.resolve()

    # temporary change working directory
    monkeypatch.chdir(tmp_path)
    pymchelper.utils.mcscripter.main([str(full_path_to_config)])
    logger.debug(f"current working directory {os.getcwd()}")
    assert Path('wdir', '1H').exists()
    if config_path == Configs.full.relpath:
        assert Path(tmp_path, 'wdir', '1H', '0246.000', 'beam.dat').exists()


def served_values(table_dict: dict, const_dict: dict, loop_key: str) -> list:
    """Loop values and energy spreads served by Template.prepare for a single table line"""
    config = pymchelper.utils.mcscripter.Config(const_dict=const_dict, table_dict=table_dict)
    served = []
    for current_dict in pymchelper.utils.mcscripter.Template.prepare(config):
        served.append((current_dict.get(loop_key), current_dict.get('DE_')))
    return served


def test_energy_spread_of_served_energy():
    """DE_ is computed from the energy it is served with, not from the next step"""
    table_dict = {'NAME': ['1H'], 'E_MIN': ['66.0'], 'E_MAX': ['70.0'], 'E_STEP': ['2.0']}
    served = served_values(table_dict, {'DE_FACTOR': '0.01'}, 'E_')
    assert served == [(66.0, '0.660'), (68.0, '0.680'), (70.0, '0.700')]


def test_last_step_is_kept():
    """Float steps do not drop the last value, 1.0 to 2.0 in 0.1 steps gives 11 values"""
    table_dict = {'NAME': ['x'], 'E_MIN': ['1.0'], 'E_MAX': ['2.0'], 'E_STEP': ['0.1']}
    energies = [energy for energy, _ in served_values(table_dict, {}, 'E_')]
    assert len(energies) == 11
    assert energies[-1] == pytest.approx(2.0)


def test_loop_key_with_letters_of_min_suffix():
    """Only the MIN suffix is removed from the key name, NSTAT_MIN gives the NSTAT_ loop key"""
    table_dict = {'NAME': ['x'], 'NSTAT_MIN': ['1000'], 'NSTAT_MAX': ['3000'], 'NSTAT_STEP': ['1000']}
    numbers_of_primaries = [value for value, _ in served_values(table_dict, {}, 'NSTAT_')]
    assert numbers_of_primaries == [1000.0, 2000.0, 3000.0]


def test_energy_written_to_beam_file(tmp_path: Path):
    """Loop values are written as numbers into the generated files"""
    config = pymchelper.utils.mcscripter.read_config(path=Configs.full.relpath)
    template = pymchelper.utils.mcscripter.read_template(cfg=config)
    template.write(tmp_path, config)

    beam_file_lines = Path(tmp_path, 'wdir', '1H', '0246.000', 'beam.dat').read_text().splitlines()
    tmax0_line = ''
    for line in beam_file_lines:
        if line.startswith('TMAX0'):
            tmax0_line = line
    tokens = tmax0_line.split()
    assert tokens[1] == '246.000'
    assert tokens[2] == '2.460'


def test_all_combinations_of_two_loop_keys(tmp_path: Path):
    """Two loop keys in one table line give a directory for every combination of their values"""
    template_directory = Path(tmp_path, 'template')
    template_directory.mkdir()
    Path(template_directory, 'beam.dat').write_text('TMAX0 ${E_}    ${DE_}\nNSTAT ${NSTAT_} -1\n')
    config_path = Path(tmp_path, 'config.cfg')
    config_path.write_text('TDIR = template\n'
                           'WDIR = wdir/${NAME}/${E_}_${NSTAT_}\n'
                           'FILES = beam.dat\n'
                           'DE_FACTOR = 0.01\n'
                           'NAME E_MIN E_MAX E_STEP NSTAT_MIN NSTAT_MAX NSTAT_STEP\n'
                           '1H   60.0  70.0  10.0   1000      2000      1000\n')
    config = pymchelper.utils.mcscripter.read_config(path=config_path)
    template = pymchelper.utils.mcscripter.read_template(cfg=config)
    template.write(tmp_path, config)

    expected_beam_file_tokens = {
        '0060.000_1000.000': ['TMAX0', '60.000', '0.600', 'NSTAT', '1000.000', '-1'],
        '0060.000_2000.000': ['TMAX0', '60.000', '0.600', 'NSTAT', '2000.000', '-1'],
        '0070.000_1000.000': ['TMAX0', '70.000', '0.700', 'NSTAT', '1000.000', '-1'],
        '0070.000_2000.000': ['TMAX0', '70.000', '0.700', 'NSTAT', '2000.000', '-1'],
    }
    generated_directories = set()
    for directory in Path(tmp_path, 'wdir', '1H').iterdir():
        generated_directories.add(directory.name)
    assert generated_directories == set(expected_beam_file_tokens)
    for directory_name, expected_tokens in expected_beam_file_tokens.items():
        beam_file_content = Path(tmp_path, 'wdir', '1H', directory_name, 'beam.dat').read_text()
        assert '${' not in beam_file_content
        assert beam_file_content.split() == expected_tokens
