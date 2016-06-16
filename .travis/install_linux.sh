#!/usr/bin/env bash

set -x # Print command traces before executing command

set -e # Exit immediately if a simple command exits with a non-zero status.

set -o pipefail # Return value of a pipeline as the value of the last command to
                # exit with a non-zero status, or zero if all commands in the
                # pipeline exit successfully.

# check ubuntu version
lsb_release -a

pip install --upgrade virtualenv$VENVVER pip$PIPVER setuptools tox wheel

if [[ $TOXENV == py32 ]];
then
  pip install git+https://github.com/grzanka/python-versioneer.git@support_python32
else
  pip install --upgrade versioneer
fi
pip install -r requirements.txt
