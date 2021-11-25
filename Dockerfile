# test with `docker-compose up -d --build`

FROM quay.io/pypa/manylinux2010_x86_64

RUN yum install -y wget 

WORKDIR /tmp/install_python

RUN wget https://www.python.org/ftp/python/3.9.9/Python-3.9.9.tgz
RUN tar -zxvf Python-3.9.9.tgz

WORKDIR /tmp/install_python/Python-3.9.9

RUN yum install -y openssl-devel libffi-devel

RUN ./configure --enable-optimizations

RUN make -j4

RUN make install

RUN /usr/local/bin/pip3 install pyinstaller

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