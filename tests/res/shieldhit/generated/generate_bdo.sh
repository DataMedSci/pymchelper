#!/usr/bin/env bash
# run from main project directory
WORKDIR=tests/res/shieldhit/generated
PYTHONPATH=. python $WORKDIR/generate_detect.py $WORKDIR
for EST in "cyl" "geomap" "msh" "plane" "zone"
do
# single
  mkdir -p $WORKDIR/single/$EST
  cp ${WORKDIR}/mat.dat ${WORKDIR}/single/${EST}/
  cp ${WORKDIR}/beam.dat ${WORKDIR}/single/${EST}/
  cp ${WORKDIR}/geo.dat ${WORKDIR}/single/${EST}/
  shieldhit -n1000 -d ${WORKDIR}/detect_${EST}.dat ${WORKDIR}/single/${EST}
  rm ${WORKDIR}/single/${EST}/for*
  rm ${WORKDIR}/single/${EST}/*.dat
# many
  mkdir -p $WORKDIR/many/$EST
  cp ${WORKDIR}/mat.dat ${WORKDIR}/many/${EST}/
  cp ${WORKDIR}/beam.dat ${WORKDIR}/many/${EST}/
  cp ${WORKDIR}/geo.dat ${WORKDIR}/many/${EST}/
  shieldhit -n1000 -N1 -d ${WORKDIR}/detect_${EST}.dat ${WORKDIR}/many/${EST}
  shieldhit -n1000 -N2 -d ${WORKDIR}/detect_${EST}.dat ${WORKDIR}/many/${EST}
  shieldhit -n1000 -N3 -d ${WORKDIR}/detect_${EST}.dat ${WORKDIR}/many/${EST}
  rm ${WORKDIR}/many/${EST}/for*
  rm ${WORKDIR}/many/${EST}/*.dat
done