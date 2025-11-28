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

To install as well `plan2sobp` program type: ``pip install "pymchelper[dicom]"``


Python package (Debian based Linux)
-----------------------------------

Deb packages are produced for 64-bit Debian-based Linux distributions (Debian 12 or newer, Ubuntu 20.04 or newer).
They contain a limited set of **pymchelper** functionality, mainly only the executable files.
The files we provide in `deb` packages have no dependency on Python interpreter, therefore can run on quite old Linux distributions.
With binary files there is no chance to use **pymchelper** as a Python library.

**Note:** The Python package (via pip) supports Linux, Windows, and macOS. Deb packages are Linux-only.

We are maintaining our repository on Github Pages service. To add this repository on you system, download our GPG key and add an entry to `sources.list` directory::


   wget -qO - https://datamedsci.github.io/deb_package_repository/public.gpg | sudo gpg --dearmor -o /usr/share/keyrings/datamedsci-archive-keyring.gpg


Then add the repository to your APT sources::


   echo "deb [signed-by=/usr/share/keyrings/datamedsci-archive-keyring.gpg] https://datamedsci.github.io/deb_package_repository/ stable main" | sudo tee /etc/apt/sources.list.d/datamedsci.list


Finally run `apt update` and install `pymchelper` metapackage (which should install all required packages for the executables that we ship)::


   sudo apt update


Then install pymchelper::


   sudo apt install pymchelper
