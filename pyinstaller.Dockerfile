# build image with `docker-compose up -d --build`

FROM centos:6

# check glibc version 
# according to https://sourceware.org/glibc/wiki/Glibc%20Timeline
# glibc v2.12 dates back to 2010.05.03
RUN rpm -q glibc
RUN ldd --version

# Centos 6 is EOL and is no longer available from the usual mirrors, so switch
# to https://vault.centos.org
RUN sed -i 's/enabled=1/enabled=0/g' /etc/yum/pluginconf.d/fastestmirror.conf && \
    sed -i 's/^mirrorlist/#mirrorlist/g' /etc/yum.repos.d/*.repo && \
    sed -i 's;^#baseurl=http://mirror;baseurl=https://vault;g' /etc/yum.repos.d/*.repo

# installation of all dependencies
RUN yum install -y wget perl gcc zlib-devel \
 && yum clean all
RUN yum groupinstall -y "Development Tools" \
 && yum clean all

# check glibc version
RUN rpm -q glibc
RUN ldd --version

# it seems libffi is not available as RPM package in yum repo, I've tried:
# RUN yum install -y wget perl gcc libffi-devel
RUN wget --no-check-certificate http://vault.centos.org/centos/6/os/x86_64/Packages/libffi-devel-3.0.5-3.2.el6.x86_64.rpm \
 && rpm -ivh  libffi-devel-3.0.5-3.2.el6.x86_64.rpm \
 && rm -f libffi*.rpm

# by default we have openssl v 1.0.1e, it can be installed using
# RUN yum install -y openssl-devel
# RUN rpm -q openssl-devel
# pypa pip server require connection via https for which newer openssl is required, hence we install it from sources

# openssl installation from sources (all in single RUN to have only one docker layer which saves disk space)
WORKDIR /tmp/
RUN mkdir install_openssl \
 && cd install_openssl \
 && wget --no-check-certificate https://www.openssl.org/source/openssl-1.0.2l.tar.gz \
 && tar xzvpf openssl-1.0.2l.tar.gz \
 && cd openssl-1.0.2l \
 && ./config --prefix=/usr/local/ssl --openssldir=/usr/local/ssl \
 && sed -i.orig '/^CFLAG/s/$/ -fPIC/' Makefile \
 && make -j16 \
 && make install \
 && rm -rf /tmp/openssl_install

# compilation of python sources (all in single RUN to have only one docker layer which saves disk space)
WORKDIR /tmp/
RUN mkdir install_python \
 && cd install_python \
 && wget https://www.python.org/ftp/python/3.9.9/Python-3.9.9.tgz \
 && tar -zxvf Python-3.9.9.tgz \
 && cd /tmp/install_python/Python-3.9.9 \
 && ./configure --enable-shared --prefix=/opt/python39 \
 && make -j16 \
 && make install \
 && cd /tmp \
 && rm -rf /tmp/install_python
ENV PATH=${PATH}:/opt/python39/bin
ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/python39/lib

# version cross-check
RUN python --version
RUN python3 --version
RUN python3 -m pip --version
RUN pip3 --version

# disable pip cache to save some space
ENV PIP_NO_CACHE_DIR=1

# pip upgrade and packages installation
RUN python3 -m pip install -U pip
RUN python3 -m pip --version
RUN pip3 --version

RUN pip install wheel setuptools

# it seems pyinstaller > 4 cannot compile on Centos6
RUN pip install "pyinstaller<4"

# # pymchelper package and deps installation
# WORKDIR /app
# COPY requirements.txt .
# COPY setup.py .
# COPY README.rst .
# COPY pymchelper pymchelper
# COPY .git .git
# RUN ls -alh
# RUN pip install --only-binary scipy,pillow -r requirements.txt
# RUN python3 pymchelper/run.py --version

# # producing single file distributions
# RUN pyinstaller -F pymchelper/run.py
# RUN pyinstaller -F pymchelper/utils/runmc.py
# RUN pyinstaller -F pymchelper/utils/pld2sobp.py
# RUN pyinstaller -F pymchelper/utils/mcscripter.py

# copy produced binary to host OS with: `docker cp installer:/app/dist/run .`


# RUN yum clean -y all