#!/bin/bash

# Print commands and their arguments as they are executed
set -x

wget --quiet https://github.com/aptly-dev/aptly/releases/download/v1.5.0/aptly_1.5.0_linux_amd64.tar.gz
tar -zxf aptly_1.5.0_linux_amd64.tar.gz

mv ./aptly_1.5.0_linux_amd64/aptly .

# cleaning
rm aptly_1.5.0_linux_amd64.tar.gz
rm --recursive --force ./aptly_1.5.0_linux_amd64
