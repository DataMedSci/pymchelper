=======================
Technical documentation
=======================

Installing from git
-------------------

To install pymchelper directly from git in a virtual environment on Linux, use the following commands.

Create and activate a virtual environment::

    python3 -m venv .venv

Activate the virtual environment::

    source .venv/bin/activate

Install from the master branch::

    pip install git+https://github.com/DataMedSci/pymchelper.git@master

Install from a specific issue branch (e.g., issue 830)::

    pip install git+https://github.com/DataMedSci/pymchelper.git@830-double-differential-sh12a-yields-convertmc-bug

To install with additional dependencies, use the extras syntax::

    pip install "git+https://github.com/DataMedSci/pymchelper.git@master#egg=pymchelper[full]"

Release management
------------------

New releases are created using Github `release feature <https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases>`_. 
When a new release is published on the *master* branch with an appropriate tag (e.g. `v1.10.10`), 
Github Actions are automatically triggered to build and upload pip and deb packages, 
as well as `release assets <https://github.com/DataMedSci/pymchelper/releases/latest>`_.


Preparing pip package
---------------------

Follow these steps to produce binary wheel package.

Install build tools::

    python -m pip install --upgrade pip build twine

Build the package::

    python -m build

Verify the built package::

    twine check dist/*

Wheel packages are automatically uploaded by github actions to `PyPI server <https://pypi.org/project/pymchelper/>`_

Preparing deb package
---------------------

Follow these steps to generate single-file executables for Linux using Nuitka.

The executables are built inside a manylinux2014 Docker container to ensure maximum compatibility::

    docker run --rm \
      -v "${PWD}:/work" \
      -w /work \
      quay.io/pypa/manylinux2014_x86_64 \
      /bin/bash -lc '
        set -e
        # Provide static libpython required by Nuitka on manylinux
        if [ -f /opt/_internal/static-libs-for-embedding-only.tar.xz ]; then
          cd /opt/_internal && tar xf static-libs-for-embedding-only.tar.xz && cd -
        fi
        PYBIN=/opt/python/cp311-cp311/bin/python
        "$PYBIN" -m pip install --upgrade pip
        # Prefer binary wheels globally for heavy deps, then install project deps
        PIP_ONLY_BINARY=:all: "$PYBIN" -m pip install --prefer-binary numpy
        PIP_ONLY_BINARY=:all: "$PYBIN" -m pip install --prefer-binary scipy
        PIP_ONLY_BINARY=:all: "$PYBIN" -m pip install --prefer-binary h5py
        "$PYBIN" -m pip install -e .[full]
        "$PYBIN" -m pip install nuitka==2.8 wheel
        
        # mcscripter
        "$PYBIN" -m nuitka \
          --standalone --onefile \
          --include-data-file=pymchelper/_version.py=pymchelper/_version.py \
          --nofollow-import-to=pytrip \
          --enable-plugin=no-qt \
          --output-dir=dist \
          --output-filename=mcscripter \
          pymchelper/utils/mcscripter.py
        
        # plan2sobp
        "$PYBIN" -m nuitka \
          --standalone --onefile \
          --include-data-file=pymchelper/_version.py=pymchelper/_version.py \
          --nofollow-import-to=pytrip \
          --enable-plugin=no-qt \
          --output-dir=dist \
          --output-filename=plan2sobp \
          pymchelper/utils/radiotherapy/plan.py
        
        # convertmc
        "$PYBIN" -m nuitka \
          --standalone --onefile \
          --include-data-file=pymchelper/_version.py=pymchelper/_version.py \
          --include-data-file=pymchelper/flair/db/card.ini=pymchelper/flair/db/card.ini \
          --include-data-file=pymchelper/flair/db/card.db=pymchelper/flair/db/card.db \
          --nofollow-import-to=pytrip \
          --nofollow-import-to=scipy \
          --enable-plugin=no-qt \
          --output-dir=dist \
          --output-filename=convertmc \
          pymchelper/run.py
      '

Run some tests.

Test the executable directly::

    ./dist/convertmc --version

Test in a Docker container::

    docker run -v `pwd`/dist:/test/ debian:stable /test/convertmc --version

Generate debian packages for all binaries.

Navigate to the debian packages directory::

    cd debian_packages

Run the package generation script::

    ./generate_deb_packages.sh convertmc mcscripter plan2sobp
    
Deb packages are automatically uploaded to `APT repository <https://github.com/DataMedSci/deb_package_repository>`_  hosted on Github Pages.

Preparing sphinx documentation
------------------------------

Sphinx documentation written reStructuredText format is stored in `docs` folder. 
It is being translated to the HTML format by Sphinx tool and automatically deployed to the Github Pages instance by Github Actions.
For details see `.github/workflows/release-pip.yml` file, in particular `generate_docs` and `deploy_docs` jobs.

To generate documentation locally, first install documentation dependencies::

    pip install -e .[docs]

Generate API documentation::

    sphinx-apidoc --output-dir docs/apidoc/ pymchelper

Build the HTML documentation::

    sphinx-build --jobs auto docs docs/_build

To view the generated documentation in your browser, start a local web server::

    python -m http.server 8000 --directory docs/_build

Then open http://localhost:8000 in your web browser to view the documentation.

