#!/bin/bash

# clean files which may be results from the previous execution of this script
rm -f ./*.tar.gz
rm -f ./*.bdo
rm -f ./*.png
rm -f ./for*
rm -f shieldhit
rm -rf shieldhit_demo.tar.gz

# fetch demo version of SHIELD-HIT12A code from main project page (extra --user-agent needed to run the code on github actions)
wget -d --user-agent="Mozilla/5.0 (Windows NT x.y; rv:10.0) Gecko/20100101 Firefox/10.0" https://shieldhit.org/download/DEMO/shield_hit12a_x86_64_demo_gfortran_v1.0.0.tar.gz -O shieldhit_demo.tar.gz

# unpack the SHIELD-HIT12A package and extract shieldhit binary to current directory
tar -zxvf shieldhit_demo.tar.gz
find . -wholename "*bin/shieldhit" -exec cp {} . \;

# check version
./shieldhit --version

# run particle transport simulation
./shieldhit

# generate images
python -m pymchelper.run image cylz.bdo default_1d.png
python -m pymchelper.run image cylz.bdo logy_1d.png --log y
python -m pymchelper.run image cylz.bdo logxy_1d.png --log x y
python -m pymchelper.run image yzmsh.bdo default_2d.png
python -m pymchelper.run image yzmsh.bdo logz_2d.png --log z
python -m pymchelper.run image yzmsh.bdo grey_2d.png --colormap Greys
