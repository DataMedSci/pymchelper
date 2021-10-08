pymchelper
==========

**pymchelper** is a toolkit for manipulating output and input files of particle transport codes,
such as FLUKA and SHIELD-HIT12A.
It provides a command line program, called **convertmc** which simplifies process of converting binary output
files to graphs, tabulated plain data files (which can be open by MS Excel) and other formats.
Toolkit can also serve as a library in Python language, which can be used by programmers and data scientists 
to read data from binary files into convenient Python objects. 
This allows further data processing using other Python tools and libraries.

**pymchelper** works under Linux, Windows and Mac OSX operating systems
(interpreter of Python programming language has to be also installed).
No programming knowledge is required from user, but basic skills in working with terminal console are needed.

Installation
------------

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

Documentation
-------------

Full pymchelper documentation can be found here: https://pymchelper.readthedocs.io/

See `Getting Started <https://pymchelper.readthedocs.org/en/stable/getting_started.html>`_ for installation and basic
information, and the `User's Guide <https://pymchelper.readthedocs.org/en/stable/user_guide.html>`_ for an overview of
how to use the project.