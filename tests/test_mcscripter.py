"""Tests for mcscripter"""
import logging
import os
from pathlib import Path
import enum
import pymchelper.utils.mcscripter
import pytest

logger = logging.getLogger(__name__)


class Configs(enum.Enum):
    """Collection of test cases for mcscripter."""
    simple = Path('simple', 'simple.cfg')
    full = Path('full', 'config.cfg')

    def __init__(self, cfg_path: Path):
        self.cfg_path = cfg_path

    @classmethod
    def list(cls):
        return list(map(lambda c: c.relpath, cls))

    @classmethod
    def names(cls):
        return list(map(lambda c: str(c.value), cls))

    @property
    def relpath(self) -> Path:
        return Path("tests", "res", "shieldhit", "mcscripter", self.cfg_path)


@pytest.fixture(scope='module')
def default_config_path() -> Path:
    """Path to the default configuration used for testing."""
    return Configs.full.relpath


@pytest.mark.parametrize("option_name", ["version", "help"])
def test_call_cmd_option(option_name: str):
    """Description needed."""
    with pytest.raises(SystemExit) as e:
        logger.info("Catching {:s}".format(str(e)))
        pymchelper.utils.mcscripter.main(['--' + option_name])
        assert e.code == 0


def test_call_cmd_no_option():
    """Description needed."""
    with pytest.raises(SystemExit) as e:
        logger.info("Catching {:s}".format(str(e)))
        pymchelper.utils.mcscripter.main([])
        assert e.code == 2


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
def test_execution(config_path: Path, monkeypatch: pytest.MonkeyPatch,
                   tmp_path: Path):
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
