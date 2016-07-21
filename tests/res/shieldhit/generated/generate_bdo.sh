#!/usr/bin/env bash
# run from main project directory
WORKDIR=tests/res/shieldhit/generated
PYTHONPATH=. python $WORKDIR/generate_detect.py $WORKDIR
for EST in "cyl" "geomap" "msh" "plane" "zone"
do
  echo $EST
  echo $WORKDIR
  mkdir -p $WORKDIR/$EST
  cp ${WORKDIR}/mat.dat ${WORKDIR}/${EST}/
  cp ${WORKDIR}/beam.dat ${WORKDIR}/${EST}/
  cp ${WORKDIR}/geo.dat ${WORKDIR}/${EST}/
  shieldhit -n1000 -d ${WORKDIR}/detect_${EST}.dat ${WORKDIR}/${EST}
done