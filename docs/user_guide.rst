.. highlight:: bash

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
   excel_converter.rst
   image_converter.rst
   gnuplot_converter.rst


Common options
--------------

**convertmc** command line program needs several options to work. 
The first one, obligatory is converter name. User might choose among: ``txt``, ``excel``, ``image``, ``gnuplot`` and ``plotdata``.

All converters accepts following options:

Input files
^^^^^^^^^^^

It is obligatory to specify location of the entities to convert. It can be a single file or a wildcard expression
(like :bash:`*.bdo`) specifying group of files.

To convert a single binary file :bash:`proton0001_fort.21` generated with Fluka to a text file you can use following command::

    convertmc txt proton0001_fort.21

Converter will automatically figure out output filename :bash:`proton0001_fort.txt`


It is also possible to merge group of files into single one to obtain better statistics. 
Let us assume we have input files :bash:`proton0001_fort.21`, :bash:`proton0002_fort.21` and :bash:`proton0003_fort.21` corresponding
to different runs but storing the output of the same scorer. To read data from these 3 files, average on-the-fly
and save output to single file, type::

   convertmc txt "proton0001_fort.*"

Again, a single file :bash:`proton0001_fort.txt` will be generated, containing averaged data from 3 binary input files.


Finally we could have many files, coming from many simulation runs and belonging to many different scorers.
**convertmc** can read list of such files, automatically group them according to scorers.
By adding :bash:`---many` flag we ask converter to scan group of files, discover sub-groups belonging to same converter
and perform averaging in each of sub-groups. Finally some number of output files will be generated (one output file
for one scorer). An example::

   convertmc txt --many "proton0001_fort.*"

Output files
^^^^^^^^^^^^

When working in single-file conversion mode or when merging group of files into a single file
 it is possible to provide a name of output file as a third argument::

    convertmc txt proton0001_fort.21 dose.txt

When using :bash:`--many` option **convertmc** will generate many files. In this case user might provide an
existing directory as a third parameter. All output files will be generated there::

    convertmc txt --many "*_fort.*" /path/to/output/dir/

Scaling factor
^^^^^^^^^^^^^^

Some of the scorers used in Monte-Carlo transport codes, such as dose or fluence dump the results per-primary-particle.
For example dose is often reported in MeV/g/prim units. These units might be hard to interpret when doing
dosimetric particle transport simulations. To report dose (or some other quantities) in more natural units knowledge
of total particles in the experiment is necessary (not to be confused with number of simulated primaries).
User can specify this number via option called :bash:`--nscale`. **convertmc** will then report dose 
(and some other quantities) in natural units and per user-provided particle number (not per single primary).
Let us assume that :bash:`proton0001_fort.21` file was obtained by simulation of 10000 protons. ::

   convertmc txt proton0001_fort.21 dose_per_prim.txt
   
will save a file :bash:`dose_per_prim.txt` with dose-per-primary and MeV/g/prim units. While::

   convertmc txt proton0001_fort.21 dose.txt --nscale 1e8

will save a file :bash:`dose.txt` with rescaled dose of :math:`10^8` protons in Gy units


Error calculation
^^^^^^^^^^^^^^^^^

In order to perform averaging converter needs to get at least two files per scorer. By default all **convertermc**
during averaging will also calculate standard deviation, which can be presented to the user in various forms:
 
 - additional column of numbers when saving data into text files (i.e. using ``txt`` converter)
 - error band on the normal plot for 1-D scoring grid (when using ``image`` and ``gnuplot`` converters)
 - additional heatmap error plot  for 2-D scoring grid (when using ``image`` and ``gnuplot`` converters)

When working in single-file mode calculation of the startand deviation is not possible and user will 
not get such information. In this case output text files will have one column less and no error band is displayed
on the plots. 

User can control presented information by means of :bash:`--error` option. When this option is not specified **convertmc**
will raport standard error if possible. Available options are:

 - :bash:`none` - no uncertainty information is reported 
 - :bash:`stderr` - standard error information is reported
 - :bash:`stddev` - standard deviation information is reported

Handling NaNs
^^^^^^^^^^^^^

In case of some simulations the results might include numbers decoded as NaN (not-a-number). 
NaN has this property that if a regular number is added to NaN then the results is again NaN
(1.0 + NaN = NaN). This property might lead to a problems when averaging. Single NaN version will
make a NaN when averaged with other 99 regular numbers.
We have a special flag in **convertmc** which will exclude NaN from averaging: if :bash:`--nan` is used
then average will be calculated only on regular numbers.

Obtaining help
^^^^^^^^^^^^^^

To get a general help instructed printed on a screen type::

   convertmc --help
   
or simply :bash:`convertmc -h`

Each of the converter comes with dedicated help page which can be printed using i.e.::

   convertmc txt --help
   

Program version
^^^^^^^^^^^^^^^

To get program version type :bash:`convertmc --version` or :bash:`convertmc -V` 


More verbose output
^^^^^^^^^^^^^^^^^^^

To get more verbose output use :bash:`-v` option (be careful, there is similar capital-V option for printing version number).
Adding :bash:`-v` or :bash:`--verbose` will make the program printing more lines of comments explaining what is doing.
By adding :bash:`-vv` even more logging output will be generated. Maximum logging level is obtained using :bash:`-vvv`.

Silent execution
^^^^^^^^^^^^^^^^

If you do like the program printing any logging output on the screen, you can use :bash:`-q` or :bash:`--quiet` option.
These options might be useful if your program is i.e. called repetitively in a script. 


Using as a library
------------------

``pymchelper`` is build around :doc:`Detector class <apidoc/pymchelper.detector>`. It provides :bash:`read` method
to get the data from binary file and is exposing to the user axis data, scoring information and data read from the file.
See an example:

.. literalinclude:: ../examples/comparison.py
   :language: python
   :linenos:
   :lines: 20-40