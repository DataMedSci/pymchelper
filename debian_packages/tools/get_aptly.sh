#!/bin/bash

# Print commands and their arguments as they are executed
set -x

wget --quiet https://github.com/aptly-dev/aptly/releases/download/v1.6.2/aptly_1.6.2_linux_amd64.zip
unzip aptly_1.6.2_linux_amd64.zip

mv ./aptly_1.6.2_linux_amd64/aptly .

# cleaning
rm aptly_1.6.2_linux_amd64.zip
rm --recursive --force ./aptly_1.6.2_linux_amd64