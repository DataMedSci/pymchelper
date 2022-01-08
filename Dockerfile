FROM ghcr.io/grzanka/centos6pyinstaller:main

# build this image with following command
# 
# docker build --tag pymchelper 
#
# run docker container to generate single-file binary in `dist` directory for pymchelper/utils/mcscripter.py
# 
# docker run -it -v `pwd`/dist:/app/dist pymchelper:latest pyinstaller --add-data 'pymchelper/VERSION:pymchelper' --onefile pymchelper/utils/mcscripter.py
#
# test if produced executable works on some old distro:
#
# docker run  -v `pwd`/dist:/test/ ubuntu:16.04 /test/mcscripter --version

# pymchelper package and deps installation
# files and directories below are needed to install pymchelper in editable mode
WORKDIR /app
COPY requirements.txt .
COPY setup.py .
COPY README.md .
COPY pymchelper pymchelper

# disable pip cache to save some space
ENV PIP_NO_CACHE_DIR=1
RUN pip install --only-binary scipy,pillow,numpy -r requirements.txt

# generate static VERSION file
COPY .git .git
RUN ls -alh .git
RUN python3 setup.py --help

# create directory for pymchelper products
RUN mkdir dist

# copy pyinstaller specification files
COPY debian_packages/single_file_executables/my_pyinstaller_utils.py .
COPY debian_packages/single_file_executables/convertmc.spec .
COPY debian_packages/single_file_executables/runmc.spec .
