#!/usr/bin/env bash

set -x # Print command traces before executing command

set -e # Exit immediately if a simple command exits with a non-zero status.

set -o pipefail # Return value of a pipeline as the value of the last command to
                # exit with a non-zero status, or zero if all commands in the
                # pipeline exit successfully.

PROJDIR=`pwd`
TMPDIR=`mktemp -d`
cd $TMPDIR
mkdir convertmc
cp -r $PROJDIR/pymchelper convertmc
python3 -m zipapp convertmc -p "/usr/bin/env python3" -m 'pymchelper.bdo2txt:main'
chmod 755 convertmc.pyz
cp convertmc.pyz $PROJDIR
cd -