FROM ghcr.io/grzanka/centos6pyinstaller:main

# build this image with following command
# 
# docker build --tag pymchelper .
#
# run docker container to generate single-file binary in `dist` directory for pymchelper/utils/mcscripter.py
# 
# docker run -it -v `pwd`/dist:/app/dist pymchelper:latest pyinstaller --add-data 'pymchelper/_version.py:pymchelper' --onefile pymchelper/utils/mcscripter.py
#
# test if produced executable works on some old distro:
#
# docker run  -v `pwd`/dist:/test/ ubuntu:16.04 /test/mcscripter --version

# pymchelper package and deps installation
# files and directories below are needed to install pymchelper in editable mode
WORKDIR /app
COPY pyproject.toml .
COPY README.md .
COPY pymchelper pymchelper

# disable pip cache to save some space
ENV PIP_NO_CACHE_DIR=1

# Install setuptools-scm and build dependencies first
RUN pip install "setuptools>=64" "setuptools-scm>=8"

# Copy git history for version detection
COPY .git .git
RUN ls -alh .git

# Install pymchelper with full dependencies in editable mode
# This will generate pymchelper/_version.py automatically via setuptools-scm
RUN pip install --only-binary h5py,scipy,pillow,numpy,matplotlib -e .[full]

# create directory for pymchelper products
RUN mkdir dist

# copy pyinstaller specification files
COPY debian_packages/single_file_executables/my_pyinstaller_utils.py .
COPY debian_packages/single_file_executables/convertmc.spec .
COPY debian_packages/single_file_executables/runmc.spec .
