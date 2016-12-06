.. highlight:: bash

.. role:: bash(code)
   :language: bash

Gnuplot
=======

Gnuplot converter is producing scripts which can be used by gnuplot tool to produce plot.
It accepts data with any 1-D and 2-D scoring grid. 
This converter might be useful for users who would like to adjust shape of the plots.

Data needed for plotting have to be generated using ``plotdata`` converter. 

Let us start with generating some data first::

    convertmc plotdata proton0001_fort.21

As expected we will get :bash:`proton0001_fort.dat` file. Now a gnuplot script can be generated::

    convertmc gnuplot proton0001_fort.21

We will get a script :bash:`proton0001_forttxt.plot` with following content::

    set term png
    set output "proton0001_fort.png"
    set title ""
    plot  './proton0001_fort.dat' u 1:2 w l lt 1 lw 2 lc -1 title 'mean value'

After running :bash:`gnuplot proton0001_fort.plot` we will get a plot

.. figure:: proton0001_forttxt.png
    :scale: 80 %
    :alt: sample file proton0001_forttxt.png generated with gnuplot converter