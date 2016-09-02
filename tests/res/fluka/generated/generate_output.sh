#!/usr/bin/env bash
# run from main project directory
WORKDIR=tests/res/fluka/generated

# loop over all directories
for dir in $WORKDIR/[a-zA-Z]*/
do
    cd $dir
    echo "in dir", ${dir}

    # loop over all input files
    for in_file in *.inp
    do
       # run fluka
       $FLUPRO/flutil/rfluka -N0 -M1 $in_file
    done

    # remove not necessary files
    rm *log *err *out ran*

    cd -
done