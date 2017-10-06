.. highlight:: bash

.. role:: bash(code)
   :language: bash

Inspect data
============

Inspector converter (not being in fact a true converter) is not producing any files,
but prints on the screen metadata of the input binary file.


An example usage
----------------

As usual we can apply standard command::

    convertmc inspect ex_yzmsh0001.bdo


We should expect to see following output on the screen::


   counter                 : '1'
   data                    : '[ 0.  0.  0. ...,  0.  0.  0.]'
   dettyp                  : 'DOSE'
   error                   : '[ 0.  0.  0. ...,  0.  0.  0.]'
   filedate                : 'Sun, 01 Oct 2017 21:13:07 +0200'
   geotyp                  : 'MSH'
   host                    : 'p2285'
   mc_code_version         : '0.6.0-dev'
   nstat                   : '500000'
   nx                      : '1'
   ny                      : '400'
   nz                      : '400'
   pages                   : '1'
   particle                : '-1'
   particle_a              : '-1'
   particle_z              : '-1'
   title                   : 'Dose'
   tripdose                : '0.0'
   tripntot                : '-1'
   units                   : '['cm', 'cm', 'cm', '(nil)', ' MeV/g/primary', 'Dose', 'Position (X)', 'Position (Y)', 'Position (Z)', '', '']'
   user                    : ''
   xmax                    : '0.1'
   xmin                    : '-0.1'
   ymax                    : '0.5'
   ymin                    : '-0.5'
   zmax                    : '4.0'
   zmin                    : '0.0'
   zone_start              : '-1'
