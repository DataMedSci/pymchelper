.. highlight:: bash

.. role:: bash(code)
   :language: bash

Plots and images
================

``image`` converter is very useful tool to quickly inspect simulation results. 
It accepts data with any 1-D and 2-D scoring grid and is producing images in PNG format with plots. 
Conversion is done using standard command::

    convertmc image --many "*.bdo"

After converting data with 1-D scoring grid, following plot can be generated

.. figure:: ex_cyl.txt.png
    :scale: 80 %
    :alt: sample file ex_cyl.txt.png generated with image converter

Data containing 2-D scoring grid are visualised as heatmap with color denoting scored value.

.. figure:: ex_yzmsh.txt.png
    :scale: 80 %
    :alt: sample file ex_yzmsh.txt.png generated with image converter


Options
-------

Colormap
^^^^^^^^

When generating heatmaps it is also possible to specify colormap. List of available colormaps is
available here: http://matplotlib.org/users/colormaps.html. By default colormap called `gnuplot2` is used.
An example plot obtained with other colormap (`Grays`) can be obtained with following command::

    convertmc image --many "*.bdo" --colormap Greys

.. figure:: ex_yzmsh2.txt.png
    :scale: 80 %
    :alt: sample file ex_yzmsh2.txt.png generated with image converter
