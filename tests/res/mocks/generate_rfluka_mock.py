#!/usr/bin/env python3

"""
Mock generator that runs rfluka with selected input file.
Then, it creates bash srcipt that will mimics rfluka for selected input file.
"""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from tests.res.mocks.libs.bash_script import generate_mock


def main(args=None) -> None:
    """
    Reads input file and runs rfluka with it.
    Then, it creates bash script that will mimics rfluka for selected input file.
    :param args: command line arguments
    """
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('fluka', help='path to rfluka executable', type=Path)
    parser.add_argument('input', help='path to fluka input file', type=Path)
    parser.add_argument('output', help='path to generated script', nargs="?", default=Path("rfluka"))

    parsed_args = parser.parse_args(args)

    fluka_path = Path(parsed_args.fluka).resolve()
    if not fluka_path.exists():
        print("Fluka executable does not exist.")
        return
    input_path = Path(parsed_args.input).resolve()
    if not input_path.exists():
        print("Input file does not exist.")
        return
    
    output_path =  Path("rfluka")
    if parsed_args.output:
        output_path = Path(parsed_args.output).resolve()

    with tempfile.TemporaryDirectory() as tmp_dir:
        shutil.copy(input_path, tmp_dir)
        dir = Path(tmp_dir)
        out = dir / "std.out"
        err = dir / "std.err"
        with (open(out, "wb") as stdout,
            open(err, "wb") as stderr):
            args = [str(fluka_path), input_path.name, "-N0", "-M1"]
            subprocess.run(args, cwd=dir, stderr=stderr, stdout=stdout)

            fluka_files = list(dir.glob("*_fort.*"))
            if not fluka_files:
                print("No fluka files found in temporary directory.")

            generate_mock(output_path, fluka_files, out, err)


if __name__ == "__main__":
    main()
