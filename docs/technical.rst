=======================
Technical documentation
=======================

Release management
------------------

New releases are created using Github `release feature <https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases>`_. 
When a new release is published on the *master* branch with an appropriate tag (e.g. `v1.10.10`), 
Github Actions are automatically triggered to build and upload pip and deb packages, 
as well as `release assets <https://github.com/DataMedSci/pymchelper/releases/latest>`_.


Preparing pip package
---------------------

Follow these steps to produce binary wheel package::

    python -m pip install --upgrade pip build twine
    python -m build
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

Run some tests::

    ./dist/convertmc --version
    docker run -v `pwd`/dist:/test/ debian:stable /test/convertmc --version

Generate debian packages for all binaries::

    cd debian_packages
    ./generate_deb_packages.sh convertmc mcscripter plan2sobp
    
Deb packages are automatically uploaded to `APT repository <https://github.com/DataMedSci/deb_package_repository>`_  hosted on Github Pages.

Preparing sphinx documentation
------------------------------

Sphinx documentation written reStructuredText format is stored in `docs` folder. 
It is being translated to the HTML format by Sphinx tool and automatically deployed to the Github Pages instance by Github Actions.
For details see `.github/workflows/release-pip.yml` file, in particular `generate_docs` and `deploy_docs` jobs.

To generate documentation locally use these commands::

    pip install -e .[docs]
    sphinx-apidoc --output-dir docs/apidoc/ pymchelper
    sphinx-build --jobs auto docs docs/_build

To view the generated documentation in your browser, you can use Python's built-in HTTP server::

    cd docs/_build
    python -m http.server 8000

Then open http://localhost:8000 in your web browser to view the documentation.

