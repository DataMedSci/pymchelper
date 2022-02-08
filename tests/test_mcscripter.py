"""
Tests for mcscripter
"""
import logging
from pathlib import Path
import tempfile

import pytest

import pymchelper.utils.mcscripter

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def config_path():
    return Path("tests", "res", "shieldhit", "mcscripter", "test.cfg")


@pytest.mark.parametrize("option_name", ["version", "help"])
def test_call_cmd_option(option_name):
    with pytest.raises(SystemExit) as e:
        logger.info("Catching {:s}".format(str(e)))
        pymchelper.utils.mcscripter.main(['--' + option_name])
        assert e.code == 0


def test_call_cmd_no_option():
    with pytest.raises(SystemExit) as e:
        logger.info("Catching {:s}".format(str(e)))
        pymchelper.utils.mcscripter.main([])
        assert e.code == 2


def test_parsing_config(config_path):
    config = pymchelper.utils.mcscripter.read_config(path=config_path)
    assert config is not None
    assert config.const_dict
    assert 'TDIR' in config.const_dict
    assert config.const_dict['TDIR'] == 'template/.'
    assert config.const_dict['FILES'] == ['beam.dat', 'detect.dat']
    assert config.table_dict
    assert config.table_dict['NAME'] == [
        '1H', '4He', '7Li', '12C', '16O', '20Ne'
    ]


def test_reading_template(config_path):
    config = pymchelper.utils.mcscripter.read_config(path=config_path)
    assert config is not None
    template = pymchelper.utils.mcscripter.read_template(cfg=config)
    assert template
    assert template.files
    assert template.files[0] == pymchelper.utils.mcscripter.McFile(
        fname='beam.dat')


def test_execution(config_path):
    out_dir = tempfile.mkdtemp()  # make temp working dir for output files
    pymchelper.utils.mcscripter.main([str(config_path)])


#     @pytest.mark.skip(reason="no way of currently testing this")
#     def test_simple(self):
#         """ Simple conversion including diagnostic output.
#         """
#         import sys
#         inp_dir = os.path.join("tests", "res", "shieldhit", "mcscripter")
#         inp_cfg = os.path.join(inp_dir, "test.cfg")
#         out_dir = tempfile.mkdtemp()  # make temp working dir for output files
#         try:
#             pymchelper.utils.mcscripter.main([inp_cfg])
#             self.assertTrue(os.path.isdir(out_dir))
#             self.assertTrue(os.path.isdir(os.path.join(out_dir, "12C")))
#             self.assertTrue(os.path.isdir(os.path.join(out_dir, "12C", "0333.100")))
#             self.assertTrue(os.path.isfile(os.path.join(out_dir, "12C", "0333.100", "beam.dat")))
#             self.assertTrue(os.path.islink(os.path.join(out_dir, "12C", "0333.100", "Water.txt")))
#             logger.info("Removing directory {:s}".format(out_dir))
#             shutil.rmtree(out_dir)
#         except AttributeError:  # on Windows with Python os.symlink is not enabled
#             self.assertEqual(os.name, 'nt')
#             self.assertEqual(sys.version_info[0], 2)
#             logger.info("Removing directory {:s}".format(out_dir))
#             shutil.rmtree(out_dir)
