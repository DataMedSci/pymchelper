.. _user_guide:

=======================
pymchelper User's Guide
=======================

.. rubric:: pytrip object model, description of classes, examples

Converter
=========

TODO

Using pymchelper as a library
=============================

The full potential of PyTRiP is exposed when using it as a library.

Using the `dir()` and `help()` methods, you may explore what functions are available, check also the index and module tables found in this documentation. 

CT and Dose data are handled by the "CtxCube" and "DosCube" classes, respectively. Structures (volume of interests) are handled by the VdxCube class.
For instance, when a treatment plan was made the resulting 3D dose distribution (and referred to as a "DosCube").

    >>> import pytrip as pt
    >>> dc = pt.DosCube()
    >>> dc.read("foobar.dos")

You can display the entire doscube by simply printing its string
(str or repr) value::

    >>> dc
    ....

We recommend you to take a look at the :doc:`Examples </examples>` and browse the :ref:`modindex` page.
