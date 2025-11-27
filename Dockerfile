FROM quay.io/pypa/manylinux2014_x86_64

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

## Build a shared-lib Python (PyInstaller requires libpythonX.Y.so)
ENV PYTHON_VERSION=3.11.8
RUN yum install -y gcc make openssl-devel bzip2-devel libffi-devel zlib-devel xz-devel sqlite-devel && \
	curl -fsSLO https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz && \
	tar -xf Python-${PYTHON_VERSION}.tgz && \
	cd Python-${PYTHON_VERSION} && \
	./configure --enable-optimizations --enable-shared --with-ensurepip=install --prefix=/opt/python-shared && \
	make -j"$(nproc)" && \
	make install && \
	cd /app && \
	rm -rf /Python-${PYTHON_VERSION}* && \
	echo "/opt/python-shared/lib" > /etc/ld.so.conf.d/python-shared.conf && ldconfig

ENV PATH=/opt/python-shared/bin:$PATH \
	LD_LIBRARY_PATH=/opt/python-shared/lib:$LD_LIBRARY_PATH \
	PYTHONDONTWRITEBYTECODE=1 \
	PIP_NO_CACHE_DIR=1

# Upgrade pip
RUN python3.11 -m pip install --upgrade pip

# Install setuptools-scm and build dependencies first
RUN python3.11 -m pip install "setuptools>=64" "setuptools-scm>=8" wheel pyinstaller

# Copy git history for version detection
COPY .git .git
RUN ls -alh .git

# Install pymchelper with full dependencies in editable mode (dynamic versioning writes _version.py)
RUN python3.11 -m pip install --only-binary h5py,scipy,pillow,numpy,matplotlib -e .[full]

# create directory for pymchelper products
RUN mkdir dist

# copy pyinstaller specification files
COPY debian_packages/single_file_executables/my_pyinstaller_utils.py .
COPY debian_packages/single_file_executables/convertmc.spec .
COPY debian_packages/single_file_executables/runmc.spec .
