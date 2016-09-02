#!/usr/bin/env bash
# run from main project directory
WORKDIR=tests/res/fluka/generated
PYTHONPATH=. python $WORKDIR/generate_input.py $WORKDIR
