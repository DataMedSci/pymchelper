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

Follow these steps to generate single-file executables for Linux using pyinstaller::

    docker build --tag pymchelper .
    docker run --volume `pwd`/dist:/app/dist pymchelper:latest pyinstaller convertmc.spec
    docker run --volume `pwd`/dist:/app/dist pymchelper:latest pyinstaller runmc.spec
    docker run --volume `pwd`/dist:/app/dist pymchelper:latest pyinstaller --add-data 'pymchelper/VERSION:pymchelper' --onefile --name pld2sobp pymchelper/utils/pld2sobp.py
    docker run --volume `pwd`/dist:/app/dist pymchelper:latest pyinstaller --add-data 'pymchelper/VERSION:pymchelper' --onefile --name mcscripter pymchelper/utils/mcscripter.py

Run some tests::

    ./dist/convertmc --version
    docker run  -v `pwd`/dist:/test/ ubuntu:12.04 /test/convertmc --version

Generate debian packages for all binaries::

    cd debian_packages
    ./generate_deb_packages.sh convertmc runmc pld2sobp mcscripter
    
Deb packages are automatically uploaded to `APT repository <https://github.com/DataMedSci/deb_package_repository>`_  hosted on Github Pages.
