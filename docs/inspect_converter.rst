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

    convertmc inspect ex_dose.bdo


We should expect to see following output on the screen::


   INFO:pymchelper.readers.shieldhit:Reading: ex_dose.bdo
   dettyp                  : 'DOSE'
   filedate                : 'Fri, 06 Oct 2017 23:05:49 +0200'
   geotyp                  : 'CYL'
   host                    : 'nz61-6'
   mc_code_version         : '0.6.0-dev'
   nstat                   : '10000'
   nx                      : '1'
   ny                      : '1'
   nz                      : '1000'
   pages                   : '1'
   particle                : '-1'
   particle_a              : '-1'
   particle_z              : '-1'
   title                   : 'Dose'
   tripdose                : '0.0'
   tripntot                : '-1'
   units                   : '['cm', 'radians', 'cm', '(nil)', ' MeV/g/primary', 'Dose', 'Radius (R)', 'Angle (PHI)', 'Position (Z)', '', '']'
   xmax                    : '10.0'
   xmin                    : '0.0'
   ymax                    : '6.28318530718'
   ymin                    : '0.0'
   zmax                    : '30.0'
   zmin                    : '0.0'
   zone_start              : '-1'
   ***************************************************************************
   Data min: 3.04792e-05, max: 0.0715219



Advanced usage
--------------

Very simple ASCII-art plots can be also printed on the screen, assuming that two libraries: bashplotlib and hipsterplot
 will be installed first::

   pip install bashplotlib hipsterplot


To activate plotting additional option has to be used::

   convertmc inspect ex_dose.bdo --details
   INFO:pymchelper.readers.shieldhit:Reading: ex_dose.bdo
   dettyp                  : 'DOSE'
   filedate                : 'Fri, 06 Oct 2017 23:05:49 +0200'
   geotyp                  : 'CYL'
   host                    : 'nz61-6'
   mc_code_version         : '0.6.0-dev'
   nstat                   : '10000'
   nx                      : '1'
   ny                      : '1'
   nz                      : '1000'
   pages                   : '1'
   particle                : '-1'
   particle_a              : '-1'
   particle_z              : '-1'
   title                   : 'Dose'
   tripdose                : '0.0'
   tripntot                : '-1'
   units                   : '['cm', 'radians', 'cm', '(nil)', ' MeV/g/primary', 'Dose', 'Radius (R)', 'Angle (PHI)', 'Position (Z)', '', '']'
   xmax                    : '10.0'
   xmin                    : '0.0'
   ymax                    : '6.28318530718'
   ymin                    : '0.0'
   zmax                    : '30.0'
   zmin                    : '0.0'
   zone_start              : '-1'
   ***************************************************************************
   Data min: 3.04792e-05, max: 0.0715219
   ***************************************************************************
   Data scatter plot
       0.0691                                                            #:
       0.0644                                                            |.
       0.0596                                                           :.|
       0.0548                                                           # .
       0.0501                                                           # .
       0.0453                                                          #: .
       0.0405                                                         ##  :
       0.0358                                                        ##
       0.0310                                                    .###.    :
       0.0262                                            . #######        .
       0.0215                       #:.####################|               :
       0.0167 ######################### .                                  .
       0.0119                                                              |
       0.0072                                                              :
       0.0024                                                              #########
   ***************************************************************************
   Data histogram

    106|  o
    100|  o                  o
     95|  o                o o
     89|  o                ooo
     84|  o                ooo
     78|  o                ooo
     73|  o               ooooo
     67|  o              oooooo
     62|  o              oooooo
     56|  o              oooooo
     50|  o              oooooo
     45|  o             ooooooo
     39|  o             ooooooo o
     34|  o             ooooooooo
     28|  o             oooooooooo
     23|  o             oooooooooo o
     17|  o             oooooooooooo oo
     12|  o             ooooooooooooooo
      6|  o             ooooooooooooooooo o o    o
      1| ooooooo o o   ooooooooooooooooooooooooo oooooooooooooo ooo oooooooooo o
        -----------------------------------------------------------------------

   ------------------------------------
   |             Summary              |
   ------------------------------------
   |        observations: 1000        |
   |       min value: 0.000030        |
   |         mean : 0.020207          |
   |       max value: 0.071522        |
   ------------------------------------
