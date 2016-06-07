#!/usr/bin/env bash

set -x # Print command traces before executing command

set -e # Exit immediately if a simple command exits with a non-zero status.

set -o pipefail # Return value of a pipeline as the value of the last command to
                # exit with a non-zero status, or zero if all commands in the
                # pipeline exit successfully.

pip install -rrequirements.txt
pip install coverage
pip install codeclimate-test-reporter
pip install pytest-cov

python -V
py.test --cov

set +x
codeclimate-test-reporter
set -x