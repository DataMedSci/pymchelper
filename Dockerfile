FROM ghcr.io/grzanka/centos6pyinstaller:main


# pymchelper package and deps installation
WORKDIR /app
COPY requirements.txt .

# disable pip cache to save some space
ENV PIP_NO_CACHE_DIR=1
RUN pip install --only-binary scipy,pillow -r requirements.txt

# files and directories below are needed to install pymchelper in editable mode
COPY setup.py .
COPY README.rst .
COPY pymchelper pymchelper
COPY .git .git

RUN python3 pymchelper/run.py --version

RUN mkdir dist

# # producing single file distributions
#RUN pyinstaller -F pymchelper/run.py
#RUN pyinstaller -F pymchelper/utils/runmc.py
#RUN pyinstaller -F pymchelper/utils/pld2sobp.py
#RUN pyinstaller -F pymchelper/utils/mcscripter.py

# generate images using 
# docker run -it -v `pwd`/dist:/app/dist 60b000a9b0db pyinstaller --add-data 'pymchelper/VERSION:pymchelper' -F pymchelper/utils/mcscripter.py
# test if produced:
# ./dist/mcscripter --version

# copy produced binary to host OS with: `docker cp installer:/app/dist/run .`
# pyinstaller --add-data 'pymchelper/VERSION:pymchelper' -F pymchelper/utils/mcscripter.py