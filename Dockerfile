FROM quay.io/pypa/manylinux2010_x86_64

RUN yum install -y rh-python36-python-devel

RUN scl enable rh-python36 -- pip install -U pip
RUN scl enable rh-python36 -- pip --version
RUN scl enable rh-python36 -- python --version
RUN scl enable rh-python36 -- pip install wheel
RUN scl enable rh-python36 -- pip install pyinstaller

WORKDIR /app
COPY ./requirements.txt ./
#COPY ./pymchelper/* ./

#RUN scl enable rh-python36 -- pip install --only-binary scipy,pillow -r requirements.txt
#RUN scl enable rh-python36 -- pip install --only-binary scipy,pillow -r requirements.txt