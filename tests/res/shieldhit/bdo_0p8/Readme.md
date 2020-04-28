Sample files for new bdo-reader. Outputs both txt and bdo-versions.
Curently, something is broken in the 30_diff-file.
125 MeV proton beam on 20 x 20 x 20 cm³ water target along z.

Test most simple cases:

    00_iddc_1d.bdo : dose scoring 20 x 20 x 20 cm³, 5 slices along z (4 cm each bin)
    01_iddc_2d.bdo : dose scoring 20 x 20 x 20 cm³, 5 slices along z and y (4 cm each bin)
    02_iddc_3d.bdo : dose scoring 20 x 20 x 20 cm³, 5 slices along z, y and x (4 cm each bin)
    03_iddc_1d.bdo : fluence scoring 20 x 20 x 20 cm³, 5 slices along z (4 cm each bin), filtered on primary particles. 

Test differential bins:

    10_diff_prm.bdo : scoring 20 x 20 x 1 cm³, 1 slice at surface. Differential spectrum (dPhi/dE), linear steps 0 - 200 MeV in 20 steps. Filtered on primary protons only.
    11_diff_z1a.bdo : scoring 20 x 20 x 1 cm³, 1 slice at surface. Differential spectrum (dPhi/dE), linear steps 0 - 200 MeV in 20 steps. 3 pages. Page 1: all protons (z=1 a=1, inc. secondary protons), Page 2: all deuterons, Page 3: all tritons. 

Test log binning:

    20_diff_prm.bdo : same as above, but in log steps, lower limit 0.1 MeV
    21_diff_z1a.bdo : same as above, but in log steps, lower limit 0.1 MeV 

Test differential energy type:

    30_diff_prm.bdo : same as 10_diff_prm.bdo, but energy in E/amu. Here, I could not get the EAMU to work, so this is the same as the 10.
