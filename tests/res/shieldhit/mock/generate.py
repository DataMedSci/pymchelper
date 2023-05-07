#!/usr/bin/env python3

"""
This script collects all shieldhit output files in the current directory and generates a bash script named shieldhit.

Generated bash script will contain all shieldhit output files as base64 encoded strings.
Running generated script will create all shieldhit output files in the current directory.
"""

import base64
import os
from pathlib import Path

__FILE_NAME_AND_CONTENT_TEMPLATE = """
FILE_NAME_{index}="{file_name}"
FILE_NAME_CONTENT_{index}="{file_content}"
sleep 1
printf '%s' "$FILE_NAME_CONTENT_{index}" | base64 -d -i > $FILE_NAME_{index}
echo "Generated $FILE_NAME_{index}"
"""

__OUTPUT_SCRIPT_NAME = "shieldhit"


def to_bash_lines(index: int, file_name: str, file_content: bytes) -> str:
    """Converts file name and content to bash lines."""
    base64_encoded_content = base64.standard_b64encode(file_content).decode("utf-8")
    return __FILE_NAME_AND_CONTENT_TEMPLATE.format(index=index, file_name=file_name,
                                                   file_content=base64_encoded_content)


def run():
    """Runs the script."""

    shieldhit_files = Path.cwd().glob("*.bdo")
    if not shieldhit_files:
        print("No shieldhit files found in current directory.")
        return

    with open(__OUTPUT_SCRIPT_NAME, "w") as f:
        f.write("#!/bin/bash\n")

        for index, file in enumerate(sorted(shieldhit_files)):
            with open(file, 'rb') as fluka_file:
                file_name = os.path.basename(file)
                file_content = fluka_file.read()
                f.write(to_bash_lines(index, file_name, file_content))
    os.chmod(__OUTPUT_SCRIPT_NAME, 0o744)


if __name__ == "__main__":
    run()
