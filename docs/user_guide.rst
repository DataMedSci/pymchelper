.. _user_guide:

.. role:: bash(code)
   :language: bash

User's Guide
============

Available converters
--------------------

Detailed documentation about available converters:

.. toctree::
   :maxdepth: 1
   
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

It is obligatory to specify location of the entities to convert. It can be a single file or a wildcard expression
(like `*.bdo`) specifying group of files.

To convert a single binary file `proton0001_fort.21` generated with Fluka to a text file you can use following command::

    convertmc txt proton0001_fort.21

Converter will automatically figure out output filename `proton0001_fort.txt`


It is also possible to merge group of files into single one to obtain better statistics. 
Let us assume we have input files `proton0001_fort.21`, `proton0002_fort.21` and `proton0003_fort.21` corresponding
to different runs but storing the output of the same scorer. To read data from these 3 files, average on-the-fly
and save output to single file, type::

   convertmc txt "proton0001_fort.*"

Again, a single file `proton0001_fort.txt` will be generated, containing averaged data from 3 binary input files.


Finally we could have many files, coming from many simulation runs and belonging to many different scorers.
**convertmc** can read list of such files, automatically group them according to scorers.
By adding `---many` flag we ask converter to scan group of files, discover sub-groups belonging to same converter
and perform averaging in each of sub-groups. Finally some number of output files will be generated (one output file
for one scorer). An example::

   convertmc txt --many "proton0001_fort.*"

Output files
^^^^^^^^^^^^

When working in single-file conversion mode or when merging group of files into a single file
 it is possible to provide a name of output file as a third argument::

    convertmc txt proton0001_fort.21 dose.txt

When using `--many` option **convertmc** will generate many files. In this case user might provide an
existing directory as a third parameter. All output files will be generated there::

    convertmc txt --many "*_fort.*" /path/to/output/dir/

Scaling factor
^^^^^^^^^^^^^^

Some of the scorers used in Monte-Carlo transport codes, such as dose or fluence dump the results `per-primary-particle`.
For example dose is often reported in `MeV/g/prim` units. These units might be hard to interpret when doing
dosimetric particle transport simulations. To report dose (or some other quantities) in more natural units knowledge
of total particles in the experiment is necessary (not to be confused with number of simulated primaries).
User can specify this number via option called `--nscale`. **convertmc** will then report dose 
(and some other quantities) in natural units and per user-provided particle number (not per single primary).
Let us assume that `proton0001_fort.21` file was obtained by simulation of 10000 protons. ::

   convertmc txt proton0001_fort.21 dose_per_prim.txt
   
will save a file `dose_per_prim.txt` with dose-per-primary and `MeV/g/prim` units. While::

   convertmc txt proton0001_fort.21 dose.txt --nscale 1e8

will save a file `dose.txt` with rescaled dose of :math:`10^8` protons in `Gy` units


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