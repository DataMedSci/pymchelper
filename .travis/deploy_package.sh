#!/usr/bin/env bash

set -x # Print command traces before executing command

set -e # Exit immediately if a simple command exits with a non-zero status.

set -o pipefail # Return value of a pipeline as the value of the last command to
                # exit with a non-zero status, or zero if all commands in the
                # pipeline exit successfully.

# make bdist universal package
pip install wheel

# first call to version method would generate VERSION  file
PYTHONPATH=. python pymchelper/run.py --version
python setup.py bdist_wheel

# makes source package
python setup.py sdist

# install the package
pip install dist/*whl

# test if it works
convertmc --version
convertmc --help
mcscripter --version
mcscripter --help

# make nuitka files
./make_single_executable.sh

# prepare for shipment
mkdir -p release_files
cp convertmc.pyz release_files/

# cleaning
rm -rf dist
rm -rf build
