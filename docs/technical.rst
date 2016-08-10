==========
pymchelper
==========

.. image:: https://img.shields.io/pypi/v/pymchelper.svg
        :target: https://pypi.python.org/pypi/pymchelper

.. image:: https://img.shields.io/travis/DataMedSci/pymchelper.svg
        :target: https://travis-ci.org/DataMedSci/pymchelper

.. image:: https://readthedocs.org/projects/pymchelper/badge/?version=latest
        :target: https://readthedocs.org/projects/pymchelper/?badge=latest
        :alt: Documentation Status

========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |travis| |appveyor|
    * - package
      - |version| |downloads| |wheel| |supported-versions| |supported-implementations|

.. |docs| image:: https://readthedocs.org/projects/pymchelper/badge/?style=flat
    :target: https://readthedocs.org/projects/pymchelper
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/DataMedSci/pymchelper.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/DataMedSci/pymchelper

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/DataMedSci/pymchelper?branch=master&svg=true
    :alt: Appveyor Build Status
    :target: https://ci.appveyor.com/project/grzanka/pymchelper

.. |version| image:: https://img.shields.io/pypi/v/pymchelper.svg?style=flat
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/pymchelper

.. |downloads| image:: https://img.shields.io/pypi/dm/pymchelper.svg?style=flat
    :alt: PyPI Package monthly downloads
    :target: https://pypi.python.org/pypi/pymchelper

.. |wheel| image:: https://img.shields.io/pypi/wheel/pymchelper.svg?style=flat
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/pymchelper

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/pymchelper.svg?style=flat
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/pymchelper

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/pymchelper.svg?style=flat
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/pymchelper

.. end-badges

Python toolkit for SHIELD-HIT12A and Fluka


Installation
============

Official version ::

    pip install pymchelper

Development version directly from GIT::

    pip install versioneer
    pip install git+https://github.com/DataMedSci/pymchelper.git

In case you don't have administrator rights, add ``--user`` flag to ``pip`` command.
In this situation converter will be probably installed in ``~/.local/bin`` directory.

To be able to use ``tripcube`` converter install also ``pytrip98`` Python package using ``pip``.

To upgrade, type::

    pip install -U pymchelper

To uninstall, simply use::

    pip uninstall pymchelper


Credits
-------

This package was created with Cookiecutter_ and the `grzanka/cookiecutter-pip-docker-versioneer`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`grzanka/cookiecutter-pip-docker-versioneer`: https://github.com/grzanka/cookiecutter-pip-docker-versioneer
