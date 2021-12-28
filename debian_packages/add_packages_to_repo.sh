#!/bin/bash

# Print commands and their arguments as they are executed
set -x

./tools/aptly repo create -distribution="stable" -component="main" main
./tools/aptly repo add main pymchelper-convertmc.deb
./tools/aptly repo add main pymchelper-runmc.deb
./tools/aptly repo add main pymchelper-pld2sobp.deb
./tools/aptly repo add main pymchelper-mcscripter.deb
./tools/aptly repo add main pymchelper.deb
./tools/aptly publish repo -batch main

ls -alh ~/.aptly/public      

mv ~/.aptly/public .

mv key_fingerprint.txt public/
mv public.gpg public/