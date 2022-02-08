"""
Tool for creating MC input files using user-specified tables and ranges.

2019 - Niels Bassler
"""

import argparse
import logging
import os
from shutil import copyfile
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Generator, List, TypeVar, Union

logger = logging.getLogger(__name__)

# path-like type hint which supports both strings and Path objects
PathLike = TypeVar("PathLike", str, bytes, os.PathLike)


@dataclass
class Config:
    """description needed"""
    # keys and values for contant assignments
    const_dict: Dict[str, Union[str, List[str]]] = field(default_factory=dict)
    # keys and values for table assignments
    table_dict: Dict[str, List[str]] = field(default_factory=dict)
    path: PathLike = None  # full path to this file (may be relative)


def read_config(path: PathLike) -> Config:
    cfg = Config(path=path)

    keys: List[str] = []
    _first_line_in_table = True

    with open(path, 'r') as input_file:
        for line in input_file:
            # skip comments
            if line.startswith('#'):
                continue

            # constant assigments
            if "=" in line:
                _v = line.split("=")
                cfg.const_dict[_v[0].strip()] = _v[1].strip()
                continue
            # check if we are starting a table
            if len(line.split()) > 0:
                if _first_line_in_table:
                    keys = line.split()
                    _first_line_in_table = False
                    # add column names
                    for key in keys:
                        cfg.table_dict[key] = []
                else:
                    # append row values
                    for key, val in zip(keys, line.split()):
                        cfg.table_dict[key].append(val)

    # replace string with comma-separated filenames with list of filenames
    if "FILES" in cfg.const_dict:
        cfg.const_dict["FILES"] = [
            filename.strip() for filename in cfg.const_dict["FILES"].split(",")
        ]
    if "SYMLINKS" in cfg.const_dict:
        cfg.const_dict["SYMLINKS"] = [
            filename.strip()
            for filename in cfg.const_dict["SYMLINKS"].split(",")
        ]

    return cfg


@dataclass
class McFile:
    """
    General MC single file object.
    This will be used for the template files as well as the generated output files.
    """
    
    path: PathLike = None  # full path to this file (may be relative)
    symlink: bool = False  # marker if file is a symlink
    lines: List[str] = field(default_factory=list)

    @property
    def fname(self):
        return Path(self.path).name

    def write(self):
        with open(self.path, 'w') as f:
            f.writelines(self.lines)

    def read(self):
        with open(self.path, 'r') as f:
            self.lines = f.readlines()

    def __post_init__(self):
        """Automatically read file contents upon object creation"""
        self.read()


@dataclass
class Template:
    """description needed"""
    files: List[McFile] = field(default_factory=list)

    @staticmethod
    def prepare(cfg: Config) -> Generator:
        # create a new dict, with all keys, but single unique values only:
        # this is the "current unique dictionary"
        # it represent a single line in config file
        # or a one of lines generated from loop variables
        current_dict = cfg.const_dict.copy()
        logger.info(current_dict)

        # loop_keys are special keys which cover a numerical range in discrete steps.
        # here we will identify them, and for each loop_key, there will be a range setup.
        # loop_keys are identified by the "_MIN" suffix:
        loop_keys = []
        for key in cfg.table_dict.keys():
            if "_MIN" in key:
                loop_keys.append(key.strip("_MIN") + "_")

        # loop over every items corresponding to every line in table section of the config directory
        for item in zip(*cfg.table_dict.values()):
            current_line_dict = dict(zip(cfg.table_dict.keys(), item))

            current_dict.update(current_line_dict)

            # now prepare the ranges for every loop_key
            for loop_key in loop_keys:
                start = float(current_line_dict[loop_key + "MIN"])
                stop = float(current_line_dict[loop_key + "MAX"])
                step = float(current_line_dict[loop_key + "STEP"])
                loop_value = start
                while loop_value <= stop:
                    # append values calculated for the loop
                    current_dict[loop_key] = loop_value
                    loop_value += step

                    # set the relative energy spread:
                    if loop_key == 'E_' and "DE_FACTOR" in current_dict:
                        _de = loop_value * float(current_dict["DE_FACTOR"])
                        # HARDCODED format for DE_
                        current_dict['DE_'] = f"{_de:.3f}"

                    yield current_dict

    def write(self, working_directory: Union[PathLike, None], cfg: Config):
        for u_dict in self.prepare(cfg=cfg):
            logger.info(u_dict)
            _wd = u_dict["WDIR"]

            # check if any keys are in WDIR subsitutions
            for key in u_dict.keys():
                token = "${" + key + "}"
                if token in _wd:

                    _s = u_dict[key]
                    if isinstance(_s, float):
                        _s = f"{u_dict[key]:08.3f}"  # HARDCODED float format for directory string
                    _wd = _wd.replace(token, _s)
            work_dir = _wd

            for tf in self.files:  # tf = template filename
                output_file_path = Path(working_directory, work_dir, tf.fname)
                output_file_path.parent.mkdir(parents=True, exist_ok=True)
                if not tf.symlink:
                    output_file_path.touch()
                    # of = output file object
                    of = McFile(path=output_file_path)
                    for line in tf.lines:
                        for key in u_dict.keys():
                            token = "${" + key + "}"
                            while token in line:
                                _s = u_dict[key]
                                if isinstance(_s, float):
                                    _s = "{u_dict[key]:.3f}"  # HARDCODED float format for loop_keys
                                line = lreplace(line, token, _s)
                        of.lines.append(line)
                    # end loop over t.files
                    of.write()
                else:
                    try:
                        output_file_path.symlink_to(target=tf.path.resolve())
                    except OSError:
                        # try copying file in case creation of symbolic links fails
                        # this may be the case i.e. for Windows users without developer mode
                        # or without administrative rights
                        copyfile(src=tf.path, dst=output_file_path)


def read_template(cfg: Config) -> Template:
    tpl = Template()

    for filename in cfg.const_dict["FILES"]:
        path = Path(cfg.const_dict['TDIR'], filename)
        if not Path(cfg.const_dict['TDIR']).is_absolute():
            path = Path(cfg.path.parent, cfg.const_dict['TDIR'], filename)
        mcfile = McFile(path=path)
        tpl.files.append(mcfile)

    for filename in cfg.const_dict["SYMLINKS"]:
        path = Path(cfg.const_dict['TDIR'], filename)
        if not Path(cfg.const_dict['TDIR']).is_absolute():
            path = Path(cfg.path.parent, cfg.const_dict['TDIR'], filename)
        mcfile = McFile(path=path, symlink=True)
        tpl.files.append(mcfile)

    return tpl


def lreplace(text: str, old: str, new: str) -> str:
    """
    Left adjusted replacement of string f with string r, in string s.

    This function is implemented in order to fill in data in FORTRAN77 fields,
    which are tied to certain positions on the line, i.e. subsequent values
    may not be shifted.

    Finds string f in string s and replaces it with string r, but left adjusted, retaining line length.
    If length of r is shorter than length of f, remaining chars will be space padded.
    If length of r is larger than length of f, then characters will be overwritten.
    A copy of s with the replacement is returned.
    """
    result = old
    if old in text:
        idx = text.find(old)
        replacement = new
        if len(new) < len(old):
            replacement += " " * (len(old) - len(new))
        result = text[:idx] + replacement + text[idx + len(replacement):]
    return result


def main(args=None):
    """Main function."""
    if args is None:
        args = sys.argv[1:]

    import pymchelper
    parser = argparse.ArgumentParser()
    parser.add_argument('fconf',
                        metavar="config.txt",
                        type=argparse.FileType('r'),
                        help="path to config file.",
                        default=sys.stdin)
    parser.add_argument('-v',
                        '--verbosity',
                        action='count',
                        help="increase output verbosity",
                        default=0)
    parser.add_argument('-V',
                        '--version',
                        action='version',
                        version=pymchelper.__version__)
    args = parser.parse_args(args)

    if args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbosity > 1:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()

    cfg = read_config(path=Path(args.fconf.name))
    t = read_template(cfg=cfg)

    t.write(working_directory=Path('.'), cfg=cfg)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
