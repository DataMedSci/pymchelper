# test with `docker-compose up -d --build`

#FROM quay.io/pypa/manylinux2010_x86_64

FROM centos:6

# Centos 6 is EOL and is no longer available from the usual mirrors, so switch
# to https://vault.centos.org
RUN sed -i 's/enabled=1/enabled=0/g' /etc/yum/pluginconf.d/fastestmirror.conf && \
    sed -i 's/^mirrorlist/#mirrorlist/g' /etc/yum.repos.d/*.repo && \
    sed -i 's;^#baseurl=http://mirror;baseurl=https://vault;g' /etc/yum.repos.d/*.repo

RUN yum install -y wget perl5

WORKDIR /tmp
# download openssl - please check https://www.openssl.org/source/ for the latest 1.0.21 version.
RUN wget --no-check-certificate https://www.openssl.org/source/openssl-1.0.2l.tar.gz
RUN tar xzvpf openssl-1.0.2l.tar.gz

WORKDIR /tmp/openssl-1.0.2l

RUN yum install -y perl

RUN ./config --prefix=/usr/local/ssl --openssldir=/usr/local/ssl
#modify Makefile to include -fPIC in CFLAGS # similar to export CFLAGS=-fPIC
RUN sed -i.orig '/^CFLAG/s/$/ -fPIC/' Makefile

RUN yum install -y gcc

RUN make -j16
RUN make test
RUN make install

WORKDIR /tmp/install_python

RUN wget https://www.python.org/ftp/python/3.9.9/Python-3.9.9.tgz
RUN tar -zxvf Python-3.9.9.tgz

RUN wget --no-check-certificate http://vault.centos.org/centos/6/os/x86_64/Packages/libffi-devel-3.0.5-3.2.el6.x86_64.rpm
RUN rpm -ivh  libffi-devel-3.0.5-3.2.el6.x86_64.rpm
RUN yum install -y zlib-devel

RUN yum groupinstall -y "Development Tools"


WORKDIR /tmp/install_python/Python-3.9.9

RUN ./configure --enable-shared --prefix=/opt/python39

RUN make -j16
RUN make install 
ENV PATH=${PATH}:/opt/python39/bin
ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/python39/lib

RUN python --version
RUN python3 --version
RUN python3 -m pip --version


RUN python3 -m pip install -U pip

RUN pip install wheel

RUN python3 --version
RUN pip3 --version

RUN pip install setuptools

RUN pip install "pyinstaller<4"


WORKDIR /app
COPY requirements.txt .
COPY setup.py .
COPY README.rst .
COPY pymchelper pymchelper
COPY .git .git
RUN ls -alh

RUN pip install --only-binary scipy,pillow -r requirements.txt
RUN python3 pymchelper/run.py --version

RUN pyinstaller -F pymchelper/run.py

#RUN cp dist/run /mnt/

#ENTRYPOINT [ "/bin/bash" ] 

#RUN /usr/local/bin/pip3 install -U pip

#RUN /usr/local/bin/pip3 install wheel

#RUN /usr/local/bin/pip3 install pyinstaller

#RUN yum install -y rh-python36-python-devel

#RUN scl enable rh-python36 -- pip install -U pip
#RUN scl enable rh-python36 -- pip --version
#RUN scl enable rh-python36 -- python --version
#RUN scl enable rh-python36 -- pip install wheel
#RUN scl enable rh-python36 -- pip install pyinstaller

#WORKDIR /app
#COPY ./requirements.txt ./
#COPY ./pymchelper/* ./

#RUN scl enable rh-python36 -- pip install --only-binary scipy,pillow -r requirements.txt
#RUN scl enable rh-python36 -- pip install --only-binary scipy,pillow -r requirements.txt