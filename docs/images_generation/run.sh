#!/bin/bash

# clean files which may be results from the previous execution of this script
rm -rf ./*.tar.gz
rm -f shieldhit
rm -rf shieldhit_demo.tar.gz

# fetch demo version of SHIELD-HIT12A code from main project page (extra --user-agent needed to run the code on github actions)
wget -d --user-agent="Mozilla/5.0 (Windows NT x.y; rv:10.0) Gecko/20100101 Firefox/10.0" https://shieldhit.org/download/DEMO/shield_hit12a_x86_64_demo_gfortran_v0.9.2.tar.gz -O shieldhit_demo.tar.gz

# unpack the SHIELD-HIT12A package and extract shieldhit binary to current directory
tar -zxvf shieldhit_demo.tar.gz
find . -wholename "*bin/shieldhit" -exec cp {} . \;

# check version
./shieldhit --version

# run particle transport simulation
./shieldhit

# generate images
python -m pymchelper.run image --many "*.bdo"