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

[pypi]
repository: https://pypi.python.org/pypi
username: ${PYPIUSER}
password: ${PYPIPASS}
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

# makes source package
python setup.py sdist

# install the package
pip install dist/*whl

# test if it works
convertmc --version
convertmc --help

# upload to pypi only if tag present
if [[ $TRAVIS_TAG != "" ]]; then
    pip install -U twine
    twine --version
    twine upload -r $PYPIREPO dist/*
fi

# make nuitka files
./make_single_executable.sh