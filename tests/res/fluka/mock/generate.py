#!/usr/bin/env python3

"""
This script generates a bash script that generates mock fluka output files from files existing in selected directory.
"""

import base64
import glob
import os

__FILE_NAME_AND_CONTENT_TEMPLATE = """
FILE_NAME_{file_name_var}="{file_name}"
FILE_NAME_CONTENT_{file_name_var}="{file_content}"
sleep 1
printf '%s' "$FILE_NAME_CONTENT_{file_name_var}" | base64 -d -i > $FILE_NAME_{file_name_var}
echo "Generated $FILE_NAME_{file_name_var}"
"""

__OUTPUT_SCRIPT_NAME = "rfluka"


def to_bash_lines(file_name: str, file_content: bytes) -> str:
    base64_encoded_content = base64.standard_b64encode(file_content).decode("utf-8")
    file_name_var = file_name.upper().replace(".", "_")
    return __FILE_NAME_AND_CONTENT_TEMPLATE.format(file_name_var=file_name_var, file_name=file_name,
                                                   file_content=base64_encoded_content)


def run():
    cwd = os.curdir
    fluka_files = glob.glob(os.path.join(cwd, "*_fort.*"))
    if not len(fluka_files):
        print("No fluka files found in current directory.")
        exit(1)
    with open(__OUTPUT_SCRIPT_NAME, "w") as f:
        f.write("#!/bin/bash\n")

        for file in sorted(fluka_files):
            with open(file, 'rb') as fluka_file:
                file_name = os.path.basename(file)
                file_content = fluka_file.read()
                f.write(to_bash_lines(file_name, file_content))
    os.chmod(__OUTPUT_SCRIPT_NAME, 0o744)

if __name__ == "__main__":
    run()