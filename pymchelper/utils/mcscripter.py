import os
import sys
import logging

import numpy as np

logger = logging.getLogger(__name__)


class Config():
    """
    Reading the config file.
    """
    def __init__(self, fn):
        with open(fn) as file:
            self.lines = file.readlines()
            self.parse()

    def parse(self):
        """
        parse configuration file
        """

        self.c_dict = {}  # list of contant assignments
        self.t_dict = {}  # list of contant assignments

        keys = []
        vals = []

        _first_line_in_table = True

        for line in self.lines:
            # skip comments
            if line[0] == '#':
                continue

            # constant assigments
            if "=" in line:
                _v = line.split("=")
                self.c_dict[_v[0].strip()] = _v[1].strip()
                continue

            # check if we are starting a table
            if len(line.split()) > 0:
                if _first_line_in_table:
                    keys = line.split()
                    _first_line_in_table = False
                else:
                    vals.append(line.split())

        print("keys and vals", keys, vals)

        # after parsing all lines setup the variable table, if it exists:
        if keys and vals:
            for i, key in enumerate(keys):
                self.t_dict[key] = [val[i] for val in vals]

        _f = []
        for item in self.c_dict["FILES"].split(","):
            _f.append(item.strip())
        self.c_dict["FILES"] = _f

        _f = []
        for item in self.c_dict["SYMLINKS"].split(","):
            _f.append(item.strip())
        self.c_dict["SYMLINKS"] = _f


class McFile():
    """
    General MC single file object
    """
    def __init__(self):
        self.fname = ""  # filename
        self.path = ""   # full path
        self.lines = []  # list of lines inside this file
        self.symlink = False  # marker if file is a symlink
        self.tdir = ""

    def write(self):
        """
        Write self to disk, create symlink if that is the case.
        """
        # check if target directory exists, create it, if not.
        try:
            os.makedirs(os.path.dirname(self.path))
        except FileExistsError:
            pass

        print(self.path)

        if self.symlink:
            link_file = os.path.join(self.tdir, self.fname)
            link_name = os.path.join(self.path)
            try:
                os.symlink(link_file, link_name)
            except FileExistsError:
                pass
        else:
            with open(self.path, 'w') as file:
                file.writelines(self.lines)


class Template():
    """
    Read all files and symlinks specified in the config file, and place them in a list of McFile objects.
    """
    def __init__(self, cfg):
        self.files = []
        self.read(cfg)

    def read(self, cfg):
        """
        """

        flist = cfg.c_dict["FILES"] + cfg.c_dict["SYMLINKS"]

        for f in flist:
            tf = McFile()
            tf.fname = f
            tf.path = os.path.join(cfg.c_dict["TDIR"], f)
            tf.tdir = cfg.c_dict["TDIR"]

            with open(tf.path) as _file:
                tf.lines = _file.readlines()

            tf.symlink = False
            if f in cfg.c_dict["SYMLINKS"]:
                tf.symlink = True
            self.files.append(tf)


class Generator():
    """
    """
    def __init__(self, t, cfg):
        # create a new dict, with all keys, but single unique values only:
        # this is the "current dictionary"
        dict = cfg.c_dict.copy()

        loop_keys = []
        for key in cfg.t_dict.keys():
            if "_MIN" in key:
                loop_keys.append(key.strip("_MIN") + "_")

        # reuse any key from table
        _vals = cfg.t_dict[key]
        for i, val in enumerate(_vals):
            for key in cfg.t_dict.keys():
                dict[key] = cfg.t_dict[key][i]  # only copy the ith value

            for loop_key in loop_keys:
                _lmin = float(cfg.t_dict[loop_key + "MIN"][i])
                _lmax = float(cfg.t_dict[loop_key + "MAX"][i])
                _lst = float(cfg.t_dict[loop_key + "STEP"][i])
                loop_vals = np.arange(_lmin, _lmax, _lst)
                for loop_val in loop_vals:
                    dict[loop_key] = loop_val

                    # at this point, the dict is fully set.
                    self.write(t, dict)

    @staticmethod
    def get_keys(s):
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
        Left adjusted replacement.
        Finds f in s and replaces it with r, but right adjusted, retaining line length.
        If r is shorter than f, remaining chars will be space padded.
        If r is larger than f, then characters will be overwritten.
        A copy of s with the replacement is returned.
        """
        if f in s:
            idx = s.find(f)
            if len(r) < len(f):
                _r = r + " " * (len(f) - len(r))
            else:
                _r = r
            text = s[:idx] + _r + s[idx + len(_r):]
            return text

    def write(self, t, dict):
        """
        Write a copy of the template, using the substitutions as specifed in dict.
        """

        _wd = dict["WDIR"]

        # check if any keys are in WDIR subsitutions

        for key in dict.keys():
            token = "${" + key + "}"
            if token in _wd:

                _s = dict[key]
                if isinstance(_s, float):
                    _s = "{:.3f}".format(dict[key])
                _wd = _wd.replace(token, _s)
        wdir = _wd

        for tf in t.files:

            of = McFile()
            of.fname = tf.fname
            of.path = os.path.join(wdir, tf.fname)

            if tf.symlink:
                continue

            for line in tf.lines:
                for key in dict.keys():
                    token = "${" + key + "}"
                    if token in line:
                        of.lines.append(self.lreplace(line, token, dict[key]))

            of.write()


def main(args):
    """
    Main function.
    """
    logger.setLevel('INFO')

    fn = args[0]

    print("filename", fn)

    cfg = Config(args[0])
    t = Template(cfg)

    for f in t.files:
        print(f.fname)

    print(cfg.c_dict)
    print(cfg.t_dict)

    t = Template(cfg)

    print("\n\n\n")
    Generator(t, cfg)


if __name__ == '__main__':
    logging.basicConfig()
    sys.exit(main(sys.argv[1:]))
