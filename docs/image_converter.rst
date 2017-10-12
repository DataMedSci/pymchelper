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

.. figure:: ex_cyl.png
    :scale: 80 %
    :alt: sample file ex_cyl.png generated with image converter

Data containing 2-D scoring grid are visualised as heatmap with color denoting scored value.

.. figure:: ex_yzmsh.png
    :scale: 80 %
    :alt: sample file ex_yzmsh.png generated with image converter


Options
-------

Logarithmic scale
^^^^^^^^^^^^^^^^^

User can also set logscale on one or more axis in the plots using `--log` option.

An example plot with logarithmic scale on Y axis::

    convertmc image --many "*.bdo" --log y

.. figure:: ex_cyl_logy.png
    :scale: 80 %
    :alt: sample file ex_cyl_logy.png generated with image converter

Scale can be also change on two axis at once::

    convertmc image --many "*.bdo" --log x y

.. figure:: ex_cyl_logxy.png
    :scale: 80 %
    :alt: sample file ex_cyl_logxy.png generated with image converter


An example plot with 2-D heatmap and logarithmic scale on Z (color) axis::

    convertmc image --many "*.bdo" --log z

.. figure:: ex_yzmsh_logz.png
    :scale: 80 %
    :alt: sample file ex_yzmsh_logz.png generated with image converter


Colormap
^^^^^^^^

When generating heatmaps it is also possible to specify colormap. List of available colormaps is
available here: http://matplotlib.org/users/colormaps.html. By default colormap called `gnuplot2` is used.
An example plot obtained with other colormap (`Greys`) can be obtained with following command::

    convertmc image --many "*.bdo" --colormap Greys

.. figure:: ex_yzmsh_grey.png
    :scale: 80 %
    :alt: sample file ex_yzmsh_grey.png generated with image converter
