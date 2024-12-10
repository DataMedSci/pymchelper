#!/bin/bash

# Print commands and their arguments as they are executed
set -x

./tools/aptly version
./tools/aptly repo create -distribution="stable" -component="main" main
./tools/aptly repo add main pymchelper-convertmc.deb
./tools/aptly repo add main pymchelper-runmc.deb
#./tools/aptly repo add main pymchelper-plan2sobp.deb  # skipping as its exceeding the 100MB limit
./tools/aptly repo add main pymchelper-mcscripter.deb
./tools/aptly repo add main pymchelper.deb
gpg --list-secret-keys
gpg --list-keys --keyid-format LONG

gpg --quick-set-expire A78079C33817ABFE9513BF99C172E55F3B9F9C5B 0

gpg --list-secret-keys
gpg --list-keys --keyid-format LONG

./tools/aptly publish repo main

ls -alh ~/.aptly/public

mv ~/.aptly/public .

mv key_fingerprint.txt public/
mv public.gpg public/
