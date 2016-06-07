#!/usr/bin/env bash

set -x # Print command traces before executing command

set -e # Exit immediately if a simple command exits with a non-zero status.

set -o pipefail # Return value of a pipeline as the value of the last command to
                # exit with a non-zero status, or zero if all commands in the
                # pipeline exit successfully.

PYPIREPO=$1

write_pypirc() {
PYPIRC=~/.pypirc

if [ -e "${PYPIRC}" ]; then
    rm ${PYPIRC}
fi

touch ${PYPIRC}
cat <<pypirc >${PYPIRC}
[distutils]
index-servers =
    pypi
    pypitest

[pypi]
repository: https://pypi.python.org/pypi
username: ${PYPIUSER}
password: ${PYPIPASS}

[pypitest]
repository: https://testpypi.python.org/pypi
username: ${PYPITESTUSER}
password: ${PYPITESTPASS}
pypirc

if [ ! -e "${PYPIRC}" ]; then
    echo "ERROR: Unable to write file ~/.pypirc"
    exit 1
fi
}

# write .pypirc file with pypi repository credentials
set +x
write_pypirc
set -x

# make bdist universal package
pip install wheel
python setup.py bdist_wheel

# upload the package to pypi repository
pip install twine
twine upload -r $PYPIREPO dist/*
