=======================
Technical documentation
=======================

Release management
------------------

New releases are created using Github `release feature <https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases>`_. 
First a release branch is created (e.g. `release/v1.10.10`). Then Github Actions are triggered which check if pip and deb packages are created correctly.
In case some problems appear, necessary fixes are being made on release branch (or sub-branches). 
When all problems are solved, release branch is being merged into *master* branch. Then a new release is added together with appropriate tag being added to a *master* branch.
Github actions will automatically trigger making and uploading of pip and deb packages, 
as well as `relase assets <https://github.com/DataMedSci/pymchelper/releases/latest>`_.


Preparing pip package
---------------------

Follow these steps to produce binary wheel package::

    pip install -r requirements.txt
    pip install wheel twine
    python -m pymchelper.run --version
    python setup.py bdist_wheel
    twine check dist/*.whl

Wheel packages are automatically uploaded by github actions to `PyPI server <https://pypi.org/project/pymchelper/>`_

Preparing deb package
---------------------

Follow these steps to generate single-file executables for Linux using Nuitka (headless matplotlib via Agg backend)::

    python -m pip install -U pip nuitka==2.8 wheel
    pip install -e .[full]

    # mcscripter
    python -m nuitka \
        --standalone --onefile \
        --include-data-file=pymchelper/_version.py=pymchelper/_version.py \
        --nofollow-import-to=pytrip \
        --enable-plugin=no-qt \
        --output-dir=dist \
        --output-filename=mcscripter \
        pymchelper/utils/mcscripter.py

    # plan2sobp (only scipy.interpolate is required)
    python -m nuitka \
        --standalone --onefile \
        --include-data-file=pymchelper/_version.py=pymchelper/_version.py \
        --nofollow-import-to=pytrip \
        --nofollow-import-to=scipy \
        --include-module=scipy.interpolate \
        --enable-plugin=no-qt \
        --output-dir=dist \
        --output-filename=plan2sobp \
        pymchelper/utils/radiotherapy/plan.py

    # runmc
    python -m nuitka \
        --standalone --onefile \
        --include-data-file=pymchelper/_version.py=pymchelper/_version.py \
        --include-data-file=pymchelper/flair/db/card.ini=pymchelper/flair/db/card.ini \
        --include-data-file=pymchelper/flair/db/card.db=pymchelper/flair/db/card.db \
        --nofollow-import-to=pytrip \
        --enable-plugin=no-qt \
        --output-dir=dist \
        --output-filename=runmc \
        pymchelper/utils/runmc.py

    # convertmc
    python -m nuitka \
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

Run some tests::

    ./dist/convertmc --version
    docker run -v `pwd`/dist:/test/ debian:stable /test/convertmc --version

Generate debian packages for all binaries::

    cd debian_packages
    ./generate_deb_packages.sh convertmc runmc plan2sobp mcscripter
    
Deb packages are automatically uploaded to `APT repository <https://github.com/DataMedSci/deb_package_repository>`_  hosted on Github Pages.

Preparing sphinx documentation
------------------------------

Sphinx documentation written reStructuredText format is stored in `docs` folder. 
It is being translated to the HTML format by Sphinx tool and automatically deployed to the Github Pages instance by Github Actions.
For details see `.github/workflows/release-pip.yml` file, in particular `docs` job.
To generate documentation locally use these commands::

    pip install docs/requirements.txt
    sphinx-build -j auto docs docs/_build

