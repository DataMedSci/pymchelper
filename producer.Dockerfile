# build image with `docker-compose up -d --build`

# move to ghcr.io

FROM pyinstaller


# pymchelper package and deps installation
WORKDIR /app
COPY requirements.txt .
COPY setup.py .
COPY README.rst .
COPY pymchelper pymchelper
COPY .git .git
RUN ls -alh

# disable pip cache to save some space
ENV PIP_NO_CACHE_DIR=1

RUN pip install --only-binary scipy,pillow -r requirements.txt
RUN python3 pymchelper/run.py --version

# # producing single file distributions
RUN pyinstaller -F pymchelper/run.py
RUN pyinstaller -F pymchelper/utils/runmc.py
RUN pyinstaller -F pymchelper/utils/pld2sobp.py
RUN pyinstaller -F pymchelper/utils/mcscripter.py

# copy produced binary to host OS with: `docker cp installer:/app/dist/run .`
