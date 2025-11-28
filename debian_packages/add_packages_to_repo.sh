#!/bin/bash

# Print commands and their arguments as they are executed
set -x

./tools/aptly version
./tools/aptly repo create -distribution="stable" -component="main" main
./tools/aptly repo add main pymchelper-convertmc.deb
#./tools/aptly repo add main pymchelper-runmc.deb   # binary not available yet
./tools/aptly repo add main pymchelper-plan2sobp.deb
./tools/aptly repo add main pymchelper-mcscripter.deb
./tools/aptly repo add main pymchelper.deb
gpg --list-keys --keyid-format LONG

./tools/aptly publish repo main

ls -alh ~/.aptly/public
# check total size of the repo
du -sh ~/.aptly/public

mv ~/.aptly/public .

mv key_fingerprint.txt public/
mv public.gpg public/
