#!/bin/bash

# Print commands and their arguments as they are executed
set -x

wget --quiet https://github.com/aptly-dev/aptly/releases/download/v1.4.0/aptly_1.4.0_linux_amd64.tar.gz
tar -zxf aptly_1.4.0_linux_amd64.tar.gz

mv ./aptly_1.4.0_linux_amd64/aptly .

# cleaning
rm aptly_1.4.0_linux_amd64.tar.gz
rm --recursive --force ./aptly_1.4.0_linux_amd64