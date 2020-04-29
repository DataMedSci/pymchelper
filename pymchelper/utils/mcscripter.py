"""
Tool for creating MC input files using user-specified tables and ranges.

2019 - Niels Bassler
"""

import os
import sys
import errno
import logging
import argparse

import numpy as np

logger = logging.getLogger(__name__)


class Config():
    """
    Reading the config file.
    """
    def __init__(self, fn):
        with open(fn) as _f:
            self.lines = _f.readlines()
            self.base_dir = os.path.dirname(fn)

            # script must run relative to location of config file.
            # this is needed, otherwise symlink creation will fail, as these are relative
            # and expect that the target exists.
            if self.base_dir:
                os.chdir(self.base_dir)
            self.parse()

    def parse(self):
        """
        Parse configuration file.
        All data are read into dicts. There are two dicts: a constant and variable (tabluated) one.
        """

        self.const_dict = {}  # list of contant assignments
        self.table_dict = {}  # list of table assignments

        keys = []
        vals = []

        _first_line_in_table = True

        for line in self.lines:
            # skip comments
            if line.startswith('#'):
                continue

            # constant assigments
            if "=" in line:
                _v = line.split("=")
                self.const_dict[_v[0].strip()] = _v[1].strip()
                continue

            # check if we are starting a table
            if len(line.split()) > 0:
                if _first_line_in_table:
                    keys = line.split()
                    _first_line_in_table = False
                else:
                    vals.append(line.split())

        # after parsing all lines setup the variable table, if it exists:
        if keys and vals:
            for i, key in enumerate(keys):
                self.table_dict[key] = [val[i] for val in vals]

        _files = []
        for item in self.const_dict["FILES"].split(","):
            _files.append(item.strip())
        self.const_dict["FILES"] = _files

        _files = []
        for item in self.const_dict["SYMLINKS"].split(","):
            _files.append(item.strip())
        self.const_dict["SYMLINKS"] = _files


class McFile():
    """
    General MC single file object.
    This will be used for the template files as well as the generated output files.
    """
    def __init__(self):
        self.fname = ""  # filename
        self.path = ""   # full path to this file (may be relative)
        self.lines = []  # list of lines inside this file
        self.symlink = False  # marker if file is a symlink
        self.templ_dir = ""  # template directory

    def write(self):
        """
        Write self to disk, create symlink if that is the case.
        """
        # check if target directory exists, create it, if not.
        try:
            os.makedirs(os.path.dirname(self.path))
        except OSError as e:  # when python 2.7 is dropped this can be replaced with FileExistsError: pass
            if e.errno == errno.EEXIST:
                pass  # silently accept existing directories
            else:
                logger.error('Directory not created.')
                raise

        if self.symlink:
            link_file = os.path.join(self.templ_dir, self.fname)
            link_target = os.path.join(self.path)
            link_name = os.path.relpath(link_file, os.path.dirname(link_target))

            try:
                os.symlink(link_name, link_target)
            except AttributeError as e:  # python 2.7 on Windows cannot create symlinks
                logger.error('Symlink not created.')
                print("Cannot create a link to the file, please check if you are using Linux or Python 3.")
                raise e
            except OSError as e:  # when python 2.7 is dropped this can be replaced with FileExistsError: pass
                if e.errno == errno.EEXIST:
                    pass  # silently accept existing symlinks
                else:
                    logger.error('Symlink not created.')
                    raise
        else:
            with open(self.path, 'w') as _f:
                logger.info("Writing {}".format(self.path))
                _f.writelines(self.lines)


class Template():
    """
    Read all files and symlinks specified in the config file, and place them in a list of McFile objects.
    """
    def __init__(self, cfg):
        self.files = []
        self.read(cfg)

    def read(self, cfg):
        """
        Reads all template files, and creates a list of McFile objects in self.files.
        """

        fname_list = cfg.const_dict["FILES"] + cfg.const_dict["SYMLINKS"]

        for fname in fname_list:
            tf = McFile()
            tf.fname = fname
            tf.path = os.path.join(cfg.const_dict["TDIR"], fname)
            tf.templ_dir = cfg.const_dict["TDIR"]

            with open(tf.path) as _f:
                tf.lines = _f.readlines()

            if fname in cfg.const_dict["SYMLINKS"]:
                tf.symlink = True
            else:
                tf.symlink = False
            self.files.append(tf)


class Generator():
    """
    This generates and writes the output files based on the loaded template files and the config file.
    """
    def __init__(self, templ, cfg):
        """
        Logic attached to the various keys is in here.
        templ is a Template object and cfg is a Config object.
        """

        # create a new dict, with all keys, but single unique values only:
        # this is the "current unique dictionary"
        u_dict = cfg.const_dict.copy()

        # loop_keys are special keys which cover a numerical range in discrete steps.
        # here we will identify them, and for each loop_key, there will be a range setup.
        # loop_keys are identified by the "_MIN" suffix:
        loop_keys = []
        for key in cfg.table_dict.keys():
            if "_MIN" in key:
                loop_keys.append(key.strip("_MIN") + "_")

        # reuse any key from table to calculate the length of the table
        # this means that the table must be homogenous, i.e. every key must have the same amount of values.
        _vals = cfg.table_dict[key]

        for i, val in enumerate(_vals):
            for key in cfg.table_dict.keys():
                u_dict[key] = cfg.table_dict[key][i]  # only copy the ith value

            # now prepare the ranges for every loop_key
            for loop_key in loop_keys:
                _lmin = float(cfg.table_dict[loop_key + "MIN"][i])
                _lmax = float(cfg.table_dict[loop_key + "MAX"][i])
                _lst = float(cfg.table_dict[loop_key + "STEP"][i])
                loop_vals = np.arange(_lmin, _lmax, _lst)
                for loop_val in loop_vals:
                    u_dict[loop_key] = loop_val

                    # set the relative energy spread:
                    if "E_" in u_dict and "DE_FACTOR" in u_dict:
                        _de = float(u_dict["E_"]) * float(u_dict["DE_FACTOR"])
                        u_dict["DE_"] = "{:.3f}".format(_de)  # HARDCODED float format for DE_

            # at this point, the dict is fully set.
            self.write(templ, u_dict)

    @staticmethod
    def get_keys(s):  # This is currently not used, but kept for future use.
        """
        return list of ${} keys in string
        """
        r = []

        if "${" in s:
            _i = [i for i, d in enumerate(s) if d == "{"]
            _ii = [i for i, d in enumerate(s) if d == "}"]

            for i in zip(_i, _ii):
                r.append(s[i[0] + 1:i[1]])
        return r

    @staticmethod
    def lreplace(s, f, r):
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
        if f in s:
            _idx = s.find(f)
            if len(r) < len(f):
                _r = r + " " * (len(f) - len(r))
            else:
                _r = r
            text = s[:_idx] + _r + s[_idx + len(_r):]
            return text

    def write(self, t, u_dict):
        """
        Write a copy of the template, using the substitutions as specifed in
        the unique dictionary u_dict.

        "Unique", means that any _MIN _MAX _STEP type variables have been set.
        """

        _wd = u_dict["WDIR"]

        # check if any keys are in WDIR subsitutions
        for key in u_dict.keys():
            token = "${" + key + "}"
            if token in _wd:

                _s = u_dict[key]
                if isinstance(_s, float):
                    _s = "{:08.3f}".format(u_dict[key])  # HARDCODED float format for directory string
                _wd = _wd.replace(token, _s)
        work_dir = _wd

        for tf in t.files:  # tf = template filename
            of = McFile()  # of = output file object
            of.fname = tf.fname
            of.path = os.path.join(work_dir, tf.fname)
            of.templ_dir = tf.templ_dir

            # symlinks should not be parsed for tokens.
            if tf.symlink:
                of.symlink = True
            else:
                of.symlink = False

                for line in tf.lines:
                    for key in u_dict.keys():
                        token = "${" + key + "}"
                        while token in line:
                            _s = u_dict[key]
                            if isinstance(_s, float):
                                _s = "{:.3f}".format(u_dict[key])  # HARDCODED float format for loop_keys
                            line = self.lreplace(line, token, _s)
                    of.lines.append(line)
            # end loop over t.files
            of.write()


def main(args=sys.argv[1:]):
    """
    Main function.
    """

    import pymchelper
    parser = argparse.ArgumentParser()
    parser.add_argument('fconf', metavar="config.txt", type=argparse.FileType('r'),
                        help="path to config file.",
                        default=sys.stdin)
    parser.add_argument('-v', '--verbosity', action='count', help="increase output verbosity", default=0)
    parser.add_argument('-V', '--version', action='version', version=pymchelper.__version__)
    args = parser.parse_args(args)

    if args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbosity > 1:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()

    cfg = Config(args.fconf.name)
    t = Template(cfg)

    Generator(t, cfg)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
