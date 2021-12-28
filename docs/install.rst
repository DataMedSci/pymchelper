.. highlight:: bash

.. role:: bash(code)
   :language: bash

Installation Guide
==================


Python package
--------------

**pymchelper** is available on PyPi, you can install install it using::

    pip install pymchelper

This would install just basic capabilities of the converter program `convertmc`: conversion to text file and inspection tool.
If you want to use more features, select a specific set of requirements:

- to enable image converter use ``pip install "pymchelper[image]"``
- to enable MS Excel converter use ``pip install "pymchelper[excel]"``
- to enable HDF converter use ``pip install "pymchelper[hdf]"``
- to enable TRiP98 converters use ``pip install "pymchelper[pytrip]"``

Multiple converters can also be enabled, i.e. by using ``pip install "pymchelper[image,excel]"``

In order to use all feautures (i.e. all available converters), use::

    pip install "pymchelper[full]"


Python package (Debian based Linux)
-----------------------------------

Deb packages are produced for 64-bit Linux distributions newer than debian 8 (jessie, released in 2015) or Ubuntu 16.04 (released in 2016).
The contain a limited set of **pymchelper** functionality, mainly only the executable files.
The files we provide in `deb` packages have no dependency on Python interpreter, therefore can run on quite old Linux distributions.
With binary files there is no chance to use **pymchelper** as a Python library.
We are maintaining our repository on Github Pages service. To add this repository on you system, download our GPG key and add an entry to `sources.list` directory::


   wget --quiet --output-document - https://datamedsci.github.io/deb_package_repository/public.gpg | sudo apt-key add -
   sudo wget --quiet --output-document /etc/apt/sources.list.d/datamedsci.list https://datamedsci.github.io/deb_package_repository/datamedsci.list

Finally run `apt update` and install `pymchelper` metapackage (which should install all required packages for the executables that we ship)::


   sudo apt update
   sudo apt install pymchelper
