#!/usr/bin/env bash

set -x # Print command traces before executing command

set -e # Exit immediately if a simple command exits with a non-zero status.

set -o pipefail # Return value of a pipeline as the value of the last command to
                # exit with a non-zero status, or zero if all commands in the
                # pipeline exit successfully.

# directory containing setup.py and project files
PROJDIR=`pwd`
PROJNAME='pymchelper'

#make single file executable with given name, for given entrypoint
make_zipapp() {
    # temporary dir, convenient for packaging
    TMPDIR=`mktemp -d`

    # go to TMPDIR
    cd $TMPDIR

    EXENAME=$1
    ENTRYPOINT=$2

    # make directory, named the same way as the single executable we want to create
    mkdir $EXENAME

    # copy there directory containing python module files
    cp -r $PROJDIR/pymchelper $EXENAME
    cp -r $PROJDIR/.git $EXENAME

    # use zipapp module to make a single executable zip file
    # zipapp was introduced in Python 3.5: https://docs.python.org/3/library/zipapp.html
    python -m zipapp $EXENAME -p "/usr/bin/env python" -m $ENTRYPOINT

    # add executable bits
    chmod ugo+x $EXENAME.pyz

    # copy back to project dir
    cp $EXENAME.pyz $PROJDIR
    cd -
}

test_zipapp() {
    # temporary dir, convenient for packaging
    TMPDIR=`mktemp -d`

    # packaged app
    APPFILE=$1

    # copy app to temp dir
    cp -r $APPFILE $TMPDIR

    # go to TMPDIR
    cd $TMPDIR

    $APPFILE --version

    $APPFILE --help

    # go back
    cd -
}

make_zipapp 'convertmc' 'pymchelper.bdo2txt:main'

test_zipapp `pwd`/'convertmc.pyz'