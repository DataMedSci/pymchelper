.. highlight:: bash

.. role:: bash(code)
   :language: bash

Installation Guide
==================

**pymchelper** provides both command-line tools (like the ``convertmc`` converter) and can be used as a Python library 
(you can import and use pymchelper in your own Python code).

Quick Installation
------------------

For most users, we recommend installing via pip in a virtual environment::


    pip install "pymchelper[full]"

The ``[full]`` option means that pymchelper is installed with all available converters (image, Excel, HDF, etc.).


Installation via pip
--------------------

**pymchelper** is available on PyPI and works on **all operating systems** (Linux, Windows, macOS).

We **strongly recommend using virtual environments** for Python package installation. 
Nowadays, system-wide or ``pip install --user`` installations are strongly discouraged due to potential conflicts 
with system packages and other Python projects.

Create and activate a virtual environment::

    python3 -m venv .venv

On Linux/macOS::

    source .venv/bin/activate

On Windows::

    .venv\Scripts\activate

Basic installation::

    pip install pymchelper

This installs basic capabilities: conversion to text files and the inspection tool.

For additional features, use these optional dependencies:

- Image converter: ``pip install "pymchelper[image]"``
- MS Excel converter: ``pip install "pymchelper[excel]"``
- HDF converter: ``pip install "pymchelper[hdf]"``
- TRiP98 converters: ``pip install "pymchelper[pytrip]"``
- DICOM support and plan2sobp: ``pip install "pymchelper[dicom]"``

Multiple features can be combined::

    pip install "pymchelper[image,excel,hdf]"

For all features::

    pip install "pymchelper[full]"

**Note:** Installing via pip provides both command-line tools and Python library access. 
However, command-line tools are not installed system-wide and require the virtual environment to be activated. 
If you need system-wide command-line tools without activating virtual environments, see the options below.


Command-line Installation for Linux (apt)
------------------------------------------

For **Debian/Ubuntu users only**, we provide APT packages for convenient system-wide installation.

**Supported distributions:** Debian 12+, Ubuntu 20.04+

**What you get:**

- Only command-line tools (``convertmc``, ``mcscripter``, ``plan2sobp``)
- System-wide installation - no virtual environment needed
- Automatic updates during normal system upgrades
- No Python interpreter required to run the tools

**Limitations:**

- Cannot be used as a Python library
- Only available for Debian-based distributions

**Why a custom repository?**

pymchelper is not included in the standard Debian/Ubuntu repositories, so you need to add our custom repository first.

Prerequisites
~~~~~~~~~~~~~

Ensure you have ``wget`` and ``gpg`` installed (usually pre-installed)::

    sudo apt update

If needed::

    sudo apt install wget gnupg

Adding the Repository
~~~~~~~~~~~~~~~~~~~~~

Download and add our GPG key::

    wget -qO - https://datamedsci.github.io/deb_package_repository/public.gpg | sudo gpg --dearmor -o /usr/share/keyrings/datamedsci-archive-keyring.gpg

Add the repository to your APT sources::

    echo "deb [signed-by=/usr/share/keyrings/datamedsci-archive-keyring.gpg] https://datamedsci.github.io/deb_package_repository/ stable main" | sudo tee /etc/apt/sources.list.d/datamedsci.list

Update package lists::

    sudo apt update

Install pymchelper::

    sudo apt install pymchelper

The tools are now available system-wide without any virtual environment activation.


Single Binary Executables (All Platforms)
------------------------------------------

We provide standalone single-file executables as release assets. These are useful for:

- **Linux users** on non-Debian distributions (Fedora, CentOS, Arch, etc.) where we don't provide native packages
- **Windows users** who want simple executable files without Python installation
- Systems where you don't have permission to install packages

**Download location:**

Visit our GitHub releases page: https://github.com/DataMedSci/pymchelper/releases/latest

Alternatively, for a specific version (e.g., v2.8.3): https://github.com/DataMedSci/pymchelper/releases/tag/v2.8.3

**Available executables:**

- ``convertmc`` - Main conversion tool
- ``mcscripter`` - Script generation tool
- ``plan2sobp`` - Treatment planning tool

**Linux:**

Download the executables and make them executable::

    chmod +x convertmc mcscripter plan2sobp

You can place them in ``~/bin`` or ``/usr/local/bin`` for system-wide access.

These executables are built with maximum compatibility and should work on a broader range of Linux distributions 
compared to the apt packages, including:

- Fedora
- CentOS/RHEL
- Arch Linux
- openSUSE
- And other distributions

**Windows:**

Download the ``.exe`` files and run them directly. No Python installation required.

**Limitations:**

- Only command-line tools (no Python library access)
- Manual updates required (not automatic like apt packages)
