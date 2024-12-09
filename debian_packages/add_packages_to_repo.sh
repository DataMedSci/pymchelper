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
./tools/aptly publish repo -batch main -gpg-key="C172E55F3B9F9C5B" -keyring="/home/runner/.gnupg/pubring.kbx" -secret-keyring="/home/runner/.gnupg/pubring.kbx"

ls -alh ~/.aptly/public

mv ~/.aptly/public .

mv key_fingerprint.txt public/
mv public.gpg public/
