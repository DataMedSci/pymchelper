#!/bin/bash

# Print commands and their arguments as they are executed
set -x

# List of executables being shipped by pymchelper
SCRIPTS_NAMES=('convertmc' 'runmc' 'pld2sobp' 'mcscripter')

# Github Pages has limit 100 MB, therefore instead of making a single package with all executables we create several smaller packages to fit in the limit
for SCRIPT in "${SCRIPTS_NAMES[@]}"; do
    # copy template to a dedicated script build directory, clean it if some leftovers are present
    rm --recursive --force pymchelper-${SCRIPT}
    mkdir --parents pymchelper-${SCRIPT}/DEBIAN
    cp control pymchelper-${SCRIPT}/DEBIAN/control
    
    # create directory to store binary executable file
    BIN_DIR=pymchelper-${SCRIPT}/usr/bin
    mkdir --parents ${BIN_DIR}

    # download latest release of binary executable file, exit in case of failure
    wget --quiet https://github.com/DataMedSci/pymchelper/releases/latest/download/${SCRIPT} --output-document=${BIN_DIR}/${SCRIPT} || exit 1;
    chmod +x ${BIN_DIR}/${SCRIPT}

    # adjust version number
    VERSION=`${BIN_DIR}/${SCRIPT} --version`
    sed --in-place "s/Version\:.*/Version\: ${VERSION}/g" pymchelper-${SCRIPT}/DEBIAN/control

    # adjust package names
    sed --in-place "s/Package\:.*/Package\: pymchelper-${SCRIPT}/g" pymchelper-${SCRIPT}/DEBIAN/control
    sed --in-place "s/Description\:.*/Description\: pymchelper ${SCRIPT}/g" pymchelper-${SCRIPT}/DEBIAN/control

    # for debian <= 7 additional flags to dpkg-deb are needed: no compression and old format: -Znone --deb-format=0.939000 

    # for all versions use newest format of deb packages, exit in case of failure
    dpkg-deb --root-owner-group --build pymchelper-${SCRIPT} pymchelper-${SCRIPT}.deb || exit 1;
done

# build meta-package

# copy template to a dedicated script build directory, clean it if some leftovers are present
rm --recursive --force pymchelper
mkdir --parents pymchelper/DEBIAN
cp control pymchelper/DEBIAN/control

# adjust version, use version of latest script from the loop above
sed -i "s/Version\:.*/Version\: ${VERSION}/g" pymchelper/DEBIAN/control

# adjust package name
sed --in-place "s/Package\:.*/Package\: pymchelper/g" pymchelper/DEBIAN/control
sed --in-place "s/Description\:.*/Description\: pymchelper/g" pymchelper/DEBIAN/control

# add dependencies
DEPS="Depends: libc6 (>= 2.12)"
for SCRIPT in "${SCRIPTS_NAMES[@]}"; do
    DEPS+=", pymchelper-${SCRIPT} (=${VERSION})"
done
sed --in-place "s/Depends\:.*/${DEPS}/g" pymchelper/DEBIAN/control

# for all versions use newest format of deb packages, exit in case of failure
dpkg-deb --root-owner-group --build pymchelper pymchelper.deb || exit 1;

ls -alh *deb