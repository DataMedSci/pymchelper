#!/bin/bash
rm -rf *.tar.gz
rm -f shieldhit
rm -rf shieldhit_demo.tar.gz
wget -d --user-agent="Mozilla/5.0 (Windows NT x.y; rv:10.0) Gecko/20100101 Firefox/10.0" https://shieldhit.org/download/DEMO/shield_hit12a_x86_64_demo_gfortran_v0.9.2.tar.gz -O shieldhit_demo.tar.gz
tar -zxvf shieldhit_demo.tar.gz
find . -wholename "*bin/shieldhit" -exec cp {} . \;
./shieldhit --version
