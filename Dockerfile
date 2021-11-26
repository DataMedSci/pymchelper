FROM ghcr.io/grzanka/centos6pyinstaller:main

# build this image with following command
# 
# docker build --tag pymchelper 
#
# run docker container to generate single-file binary in `dist` directory for pymchelper/utils/mcscripter.py
# 
# docker run -it -v `pwd`/dist:/app/dist pymchelper:latest pyinstaller --add-data 'pymchelper/VERSION:pymchelper' -F pymchelper/utils/mcscripter.py
#
# test if produced executable works on some old distro:
#
# docker run  -v `pwd`/dist:/test/ ubuntu:16.04 /test/mcscripter --version


# pymchelper package and deps installation
# files and directories below are needed to install pymchelper in editable mode
WORKDIR /app
COPY requirements.txt .
COPY setup.py .
COPY README.rst .
COPY pymchelper pymchelper
COPY .git .git

# disable pip cache to save some space
ENV PIP_NO_CACHE_DIR=1
RUN pip install --only-binary scipy,pillow -r requirements.txt

# generate static VERSION file
RUN ls -alh .git
RUN python3 setup.py --help

# create directory for pymchelper products
RUN mkdir dist
