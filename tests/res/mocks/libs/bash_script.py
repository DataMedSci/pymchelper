import base64
from pathlib import Path
from typing import List

__FILE_NAME_AND_CONTENT_TEMPLATE = """
FILE_NAME_{index}="{file_name}"
FILE_NAME_CONTENT_{index}="{file_content}"
sleep 1
printf '%s' "$FILE_NAME_CONTENT_{index}" | base64 -d > $FILE_NAME_{index}
echo "Generated $FILE_NAME_{index}"
"""


def to_bash_lines(index: int, file_name: str, file_content: bytes) -> str:
    """Converts file name and content to bash lines."""
    base64_encoded_content = base64.standard_b64encode(file_content).decode("utf-8")
    return __FILE_NAME_AND_CONTENT_TEMPLATE.format(index=index, file_name=file_name,
                                                   file_content=base64_encoded_content)


def create_script(script_name: str, files_to_save: List[Path]):
    """Creates a bash script with given name and files to save."""
    sp = Path(script_name)
    with open(sp, "w") as script:
        script.write("#!/bin/bash\n")
        for index, file in enumerate(sorted(files_to_save)):
            with open(file, 'rb') as f:
                file_name = file.name
                file_content = f.read()
                script.write(to_bash_lines(index, file_name, file_content))
    sp.chmod(0o744)