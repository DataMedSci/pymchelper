.. highlight:: bash

.. role:: bash(code)
   :language: bash

Plain text
==========

Plain text converter comes in two flavours: ``txt`` and ``plotdata``. 
It accepts data with any dimension of scoring grid: 0-D (single number), 1-D, 2-D and 3-D.

txt converter
-------------

First one (``txt``) generates 4- or 5- column text files.
After running: :bash:`convertmc txt proton0001_fort.21 dose.txt`, new file :bash:`dose.txt`
will contain: X,Y,Z coordinates, data and error column::

 0.0000000E+00  0.0000000E+00  0.5000000E-02  0.1881775795482099E-02  0.2157818940293169E-04
 0.0000000E+00  0.0000000E+00  0.1500000E-01  0.1893831696361303E-02  0.2251415707395123E-04
 0.0000000E+00  0.0000000E+00  0.2500000E-01  0.1887728041037917E-02  0.1936414681456153E-04
 0.0000000E+00  0.0000000E+00  0.3500000E-01  0.1897429465316236E-02  0.1944586725074595E-04
 (...)

When running :bash:`convertmc txt proton0001_fort.21 dose.txt --error none` fifth column will not be appended
and file contents will be following::

 0.0000000E+00  0.0000000E+00  0.5000000E-02  0.1881775795482099E-02
 0.0000000E+00  0.0000000E+00  0.1500000E-01  0.1893831696361303E-02
 0.0000000E+00  0.0000000E+00  0.2500000E-01  0.1887728041037917E-02
 0.0000000E+00  0.0000000E+00  0.3500000E-01  0.1897429465316236E-02
 (...)
 
 
plotdata converter
------------------

In the examples shown above we could see that columns corresponding to X and Y axis contain fixed number (0.0). 
It comes from the fact that the 1-dimensional scoring grid spans along the Z axis.
When plotting data from such file user needs to select third and fourth column.

**convertmc** can skip data of columns with fixed number and save to file only columns which contain 
plottable values. This can be achieved by running::

    convertmc plotdata proton0001_fort.21 dose.txt
    
We will get a file containing following data - Z axis, data and error column::

 0.5000000E-02  0.1881775795482099E-02  0.2157818940293169E-04
 0.1500000E-01  0.1893831696361303E-02  0.2251415707395123E-04
 0.2500000E-01  0.1887728041037917E-02  0.1936414681456153E-04
 0.3500000E-01  0.1897429465316236E-02  0.1944586725074595E-04
 (...)

Such file is easier to handle for plotting, as user can select only first and second column.