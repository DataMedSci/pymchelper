#!/bin/bash

set -x

../../../shieldhit/shieldhit --version

for STAT in 10 100 1000
do
    rm -rf workspace_stat${STAT}
    mkdir workspace_stat${STAT}
    for SEED in 1 2 3
    do
        ../../../shieldhit/shieldhit --silent --seedoffset=${SEED} --nstat=${STAT} -b beam.dat -g geo.dat -m mat.dat -d detect.dat workspace_stat${STAT}
    done
done
