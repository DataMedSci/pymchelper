#!/usr/bin/env python3

"""
Mock generator that runs topas with selected input file.
Then, it creates bash srcipt that will mimics topas for selected input file.
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
    Reads input file and runs topas with it.
    Then, it creates bash script that will mimics topas for selected input file.
    :param args: command line arguments
    """
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('topas', help='path to topas executable', type=Path)
    parser.add_argument('input', help='path to topas input file', type=Path)
    parser.add_argument('output', help='path to generated script', nargs="?", default=Path("topas"))

    parsed_args = parser.parse_args(args)

    topas_path = Path(parsed_args.topas).resolve()
    if not topas_path.exists():
        print("Topas executable does not exist.")
        return
    input_path = Path(parsed_args.input).resolve()
    if not input_path.exists():
        print("Input file does not exist.")
        return

    output_path = Path("topas")
    if parsed_args.output:
        output_path = Path(parsed_args.output).resolve()

    with tempfile.TemporaryDirectory() as tmp_dir:
        shutil.copy(input_path, tmp_dir)
        tmp_path = Path(tmp_dir)
        out = tmp_path / "std.out"
        err = tmp_path / "std.err"
        with open(out, "wb") as stdout, open(err, "wb") as stderr:
            fluka_args = [str(topas_path), input_path.name]
            subprocess.check_call(fluka_args, cwd=tmp_path, stderr=stderr, stdout=stdout)

            topas_files = list(tmp_path.glob("*.csv"))
            if not topas_files:
                print("No topas files found in temporary directory.")

            generate_mock(output_path, topas_files, out, err)


if __name__ == "__main__":
    main()
