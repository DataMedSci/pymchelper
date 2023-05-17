import base64
from pathlib import Path
from typing import List, Optional

__FILE_NAME_AND_CONTENT_TEMPLATE = """
OUTPUT_FILE_NAME_{index}="{file_name}"
OUTPUT_FILE_CONTENT_{index}="{file_content}"
sleep 1
printf '%s' "$OUTPUT_FILE_CONTENT_{index}" | base64 -d > $OUTPUT_FILE_NAME_{index}
"""

__STDOUT_TEMPLATE = """
STDOUT_FILE_CONTENT="{stdout}"
sleep 1
printf '%s' "$STDOUT_FILE_CONTENT" | base64 -d >&1
"""

__STDERR_TEMPLATE = """
STDERR_FILE_CONTENT="{stderr}"
sleep 1
printf '%s' "$STDERR_FILE_CONTENT" | base64 -d >&2
"""


def encode_single_file(file_number: int, file_name: str, file_content: bytes) -> str:
    """Encodes single file to bash script"""
    base64_encoded_content = base64.standard_b64encode(file_content).decode("utf-8")
    return __FILE_NAME_AND_CONTENT_TEMPLATE.format(index=file_number, file_name=file_name,
                                                   file_content=base64_encoded_content)


def generate_mock(output_path: Path, files_to_save: List[Path], stdout: Optional[Path] = None,
                  stderr: Optional[Path] = None):
    """Creates a bash script with given name and files to save."""
    with open(output_path, "w") as script:  # skipcq: PTC-W6004
        script.write("#!/bin/bash\n")
        for index, file in enumerate(sorted(files_to_save)):
            with open(file, 'rb') as f:
                file_name = file.name
                file_content = f.read()
                script.write(encode_single_file(index, file_name, file_content))

        if stdout:
            with open(stdout, 'rb') as f:
                stdout_content = f.read()
                stdout_content = base64.standard_b64encode(stdout_content).decode("utf-8")
                script.write(__STDOUT_TEMPLATE.format(stdout=stdout_content))
        if stderr:
            with open(stderr, 'rb') as f:
                stderr_content = f.read()
                stderr_content = base64.standard_b64encode(stderr_content).decode("utf-8")
                script.write(__STDERR_TEMPLATE.format(stderr=stderr_content))

    output_path.chmod(0o744)
