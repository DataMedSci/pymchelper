"""
Tool for creating MC input files using user-specified tables and ranges.

2019 - Niels Bassler
"""

import argparse
import logging
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from shutil import copyfile
from typing import Dict, Generator, List, TypeVar, Union

logger = logging.getLogger(__name__)

# path-like type hint which supports both strings and Path objects
PathLike = TypeVar("PathLike", str, bytes, os.PathLike)


@dataclass
class Config:
    """Description needed."""

    # keys and values for contant assignments
    const_dict: Dict[str, str] = field(default_factory=dict)
    # keys and values for table assignments
    table_dict: Dict[str, List[str]] = field(default_factory=dict)
    path: Path = field(
        default_factory=Path)  # full path to this file (may be relative)

    # special const dict fields:
    files: List[str] = field(default_factory=list)
    symlinks: List[str] = field(default_factory=list)


def read_config(path: PathLike, quiet: bool = True) -> Config:
    """Description needed"""
    cfg = Config(path=Path(str(path)))

    keys: List[str] = []
    _first_line_in_table = True

    with open(path, 'r') as input_file:
        for line in input_file:
            # skip comments
            if line.startswith('#'):
                continue

            # constant assigments
            if "=" in line:
                lhs_and_rhs = line.split("=")
                cfg.const_dict[lhs_and_rhs[0].strip()] = lhs_and_rhs[1].strip()
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
        cfg.files = [
            filename.strip() for filename in cfg.const_dict["FILES"].split(",")
        ]
    if "SYMLINKS" in cfg.const_dict:
        cfg.symlinks = [
            filename.strip()
            for filename in cfg.const_dict["SYMLINKS"].split(",")
        ]
    logger.debug(f"Config: {cfg}")
    if not quiet:
        print(f"Read config: {path!s}")
        print(f"\t Template dir relative directory: {cfg.const_dict['TDIR']}")
    return cfg


@dataclass
class McFile:
    """
    General MC single file object.
    This will be used for the template files as well as the generated output files.
    """

    path: Path = field(
        default_factory=Path)  # full path to this file (may be relative)
    symlink: bool = False  # marker if file is a symlink
    lines: List[str] = field(default_factory=list)

    @property
    def fname(self):
        """Description needed"""
        return Path(self.path).name

    def write(self):
        """Description needed"""
        with open(self.path, 'w') as f:
            f.writelines(self.lines)

    def read(self):
        """Description needed"""
        with open(self.path, 'r') as f:
            self.lines = f.readlines()

    def __post_init__(self):
        """Automatically read file contents upon object creation"""
        self.read()


@dataclass
class Template:
    """Description needed."""

    files: List[McFile] = field(default_factory=list)

    @staticmethod
    def prepare(cfg: Config) -> Generator:
        """Description needed."""
        # create a new dict, with all keys, but single unique values only:
        # this is the "current unique dictionary"
        # it represent a single line in config file
        # or a one of lines generated from loop variables
        current_dict: Dict[str, Union[str, float]] = dict(cfg.const_dict)

        # loop_keys are special keys which cover a numerical range in discrete steps.
        # here we will identify them, and for each loop_key, there will be a range setup.
        # loop_keys are identified by the "_MIN" suffix:
        loop_keys = []
        for key in cfg.table_dict.keys():
            if "_MIN" in key:
                loop_keys.append(key.strip("_MIN") + "_")

        if not cfg.table_dict:
            logger.debug(f"Serving {current_dict}")
            yield current_dict

        # loop over every items corresponding to every line in table section of the config directory
        for item in zip(*cfg.table_dict.values()):
            current_line_dict = dict(zip(cfg.table_dict.keys(), item))
            current_dict.update(current_line_dict)

            if not loop_keys:
                logger.debug(f"Serving {current_dict}")
                yield current_dict

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

                    logger.debug(f"Serving {current_dict}")
                    yield current_dict

    def write(self,
              working_directory: PathLike,
              cfg: Config,
              quiet: bool = True):
        """Description needed."""
        if not quiet:
            print(f"Saving generated workspace to {working_directory!s}")
        for u_dict in self.prepare(cfg=cfg):
            logger.debug(u_dict)
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
            if not work_dir:
                print(
                    f"Directory WDIR is not set in config file {cfg}, cannot proceed"
                )

            current_working_dir = Path(str(working_directory), work_dir)
            if current_working_dir.exists():
                if not quiet:
                    print(
                        f"Workspace {current_working_dir} directory exists, cleaning ..."
                    )
                shutil.rmtree(current_working_dir)
                current_working_dir.mkdir(parents=True)

            for tf in self.files:  # tf = template filename
                output_file_path = Path(current_working_dir, tf.fname)
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
                        logger.debug(
                            f'Creating link {output_file_path} -> {tf.path.resolve()}'
                        )
                        output_file_path.symlink_to(target=tf.path.resolve())
                    except OSError:
                        # try copying file in case creation of symbolic links fails
                        # this may be the case i.e. for Windows users without developer mode
                        # or without administrative rights
                        copyfile(src=tf.path, dst=output_file_path)


def read_template(cfg: Config) -> Template:
    """Description needed."""
    tpl = Template()

    for filename in cfg.files:
        path = Path(cfg.const_dict['TDIR'], filename)
        if not Path(cfg.const_dict['TDIR']).is_absolute():
            path = Path(cfg.path.parent, cfg.const_dict['TDIR'], filename)
        mcfile = McFile(path=path)
        tpl.files.append(mcfile)

    for filename in cfg.symlinks:
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
    parser.add_argument('config_path',
                        metavar="config.txt",
                        type=Path,
                        default=Path('.').absolute() / "config.txt",
                        help="config file.")
    parser.add_argument('-w',
                        '--workspace',
                        type=Path,
                        default=Path('.').absolute(),
                        help="workspace directory.")
    parser.add_argument('-V',
                        '--version',
                        action='version',
                        version=pymchelper.__version__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-q', '--quiet', action="store_true", help="quiet mode")
    group.add_argument('-v',
                       '--verbosity',
                       action='count',
                       help="increase output verbosity",
                       default=0)
    parsed_args = parser.parse_args(args)

    if parsed_args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif parsed_args.verbosity > 1:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()

    cfg = read_config(path=parsed_args.config_path, quiet=parsed_args.quiet)
    t = read_template(cfg=cfg)
    t.write(working_directory=parsed_args.workspace,
            cfg=cfg,
            quiet=parsed_args.quiet)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
