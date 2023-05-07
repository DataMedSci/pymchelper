#!/usr/bin/env python3

"""
This script collects all fluka output files in the current directory and generates a bash script named rfluka.

Generated bash script will contain all fluka output files as base64 encoded strings.
Running generated script will create all fluka output files in the current directory.
"""

from pathlib import Path

from tests.res.mocks.libs.bash_script import create_script


def run():
    """Runs the script."""
    fluka_files = list(Path.cwd().glob("*_fort.*"))
    if not fluka_files:
        print("No fluka files found in current directory.")
        return

    create_script("rfluka", fluka_files)


if __name__ == "__main__":
    run()
