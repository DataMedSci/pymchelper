#!/usr/bin/env python3

"""
Mock generator that runs shieldhit with selected input files.

Generated mock is a bash srcipt that will mimics shieldhit output for selected input files.
"""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from tests.res.mocks.libs.bash_script import generate_mock


def main(args=None) -> None:
    """
    Read input file and run rfluka.

    Then, it creates bash script that will mimics rfluka for selected input file.
    :param args: command line arguments
    """
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('shieldhit', help='path to shieldhit executable', type=Path)
    parser.add_argument('input', help='path to shieldhit input directory', type=Path)
    parser.add_argument('output', help='path to generated script', nargs="?", default=Path("shieldhit"))

    parsed_args = parser.parse_args(args)

    shieldhit_path = Path(parsed_args.shieldhit).resolve()
    if not shieldhit_path.exists():
        print("Shieldhit executable does not exist.")
        return
    input_path = Path(parsed_args.input).resolve()
    if not input_path.exists():
        print("Input directory does not exist.")
        return
    input_file_paths = list(input_path.glob("*.dat"))
    expected_files = {'beam.dat', 'detect.dat', 'geo.dat', 'mat.dat'}
    if {f.name for f in input_file_paths} != expected_files:
        print("Input directory does not contain expected files.")
        return

    output_path = Path("shieldhit")
    if parsed_args.output:
        output_path = Path(parsed_args.output).resolve()

    with tempfile.TemporaryDirectory() as tmp_dir:
        for file_path in input_file_paths:
            shutil.copy(file_path, tmp_dir)
        tmp_path = Path(tmp_dir)
        out = tmp_path / "std.out"
        err = tmp_path / "std.err"
        with open(out, "wb") as stdout, open(err, "wb") as stderr:
            shieldhit_args = [str(shieldhit_path), "-n", "1", str(tmp_dir)]
            subprocess.check_call(shieldhit_args, cwd=tmp_path, stderr=stderr, stdout=stdout)
        
            result_files = list(tmp_path.glob("*.bdo"))
            if not result_files:
                print("No generated files found in temporary directory.")

            generate_mock(output_path, result_files, out, err)


if __name__ == "__main__":
    main()
