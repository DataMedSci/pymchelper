.. _user_guide:

.. role:: bash(code)
   :language: bash

User's Guide
============

Available converters
--------------------

Detailed documentation about available converters:

.. toctree::
   :maxdepth: 2
   
   txt_converter.rst
   image_converter.rst
   gnuplot_converter.rst


Common options
--------------

**convertmc** command line program needs several options to work. 
The first one, obligatory is converter name. User might choose among: ``txt``, ``image``, ``gnuplot`` and ``plotdata``.

All converters accepts following options:

Input files
^^^^^^^^^^^

TODO

Output files
^^^^^^^^^^^^

TODO

Scaling factor
^^^^^^^^^^^^^^

TODO

Error calculation
^^^^^^^^^^^^^^^^^

TODO

Handling NaNs
^^^^^^^^^^^^^

TODO


Obtaining help
^^^^^^^^^^^^^^

To get a general help instructed printed on a screen type::

   convertmc --help
   
or simply :code:`convertmc -h`

Each of the converter comes with dedicated help page which can be printed using i.e.::

   convertmc txt --help
   

Program version
^^^^^^^^^^^^^^^

To get program version type :code:`convertmc --version` or :code:`convertmc -V` 


More verbose output
^^^^^^^^^^^^^^^^^^^

To get more verbose output use :code:`-v` option (be careful, there is similar capital-V option for printing version number).
Adding :code:`-v` or :code:`--verbose` will make the program printing more lines of comments explaining what is doing.
By adding :code:`-vv` even more logging output will be generated. Maximum logging level is obtained using :code:`-vvv`.

Silent execution
^^^^^^^^^^^^^^^^

If you do like the program printing any logging output on the screen, you can use :code:`-q` or :code:`--quiet` option.
These options might be useful if your program is i.e. called repetitively in a script. 


Using as a library
------------------

TODO