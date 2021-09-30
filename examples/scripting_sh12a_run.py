"""
This module demonstrates a parameter study with SHIELD-HIT12A particle transport simulation.
The code below is used to figure out which proton energy is needed to obtain a beam with range of 20.05 mm in liquid water.

We start with simple onion-like geometry, based on three cylinders having symmetry axis along OZ axis.
First cylinder is contained in the second one, which in turned is contained in the third one.
  - cylinder filled with liquid water, radius 10cm, spanning from 0 to 30 cm
  - vacuum cylinder, radius 15cm, spanning from 0 to 35 cm
  - black body cylinder, radius 20cm, spanning from 0 to 40 cm
We are interested only in the particle interactions in water, but nevertheless we need to define also 
enclosing vacuum and black body cylinders as is described in SHIELD-HIT12A manual: 
http://shieldhit.org/download/SHIELDHIT12A_UsersGuide.pdf

Scoring of dose is defined in the liquid water cylinder, in 3000 slabs along Z axis. 
Each slab has radius 10cm and thickness 1mm.

For physics settings we include only straggling according to Vavilov model and Moliere multiple scattering.
Nuclear reactions are switched off to speed up simulation time.

As particle source we use monoenergtic proton source located at (0,0,0), 
which is the central point of the front wall of liquid water cylinder.
Protons are emitted along OZ axis.
We will scan energies between 20 MeV and 400 MeV to figure out which energy corresponds to 20.05 mm range.

SHIELD-HIT12A cannot produce directly a single number which is a range of a beam with given energy.
As the simulation output we obtain a binary file, which is unpacked into a data structure containing:
 - binning of the dose scorer along Z axis, which in our case is a table of numbers from 0 to 30 cm (with 1mm step)
 - simulated values of the dose in each of slabs, in Gy/primary particle, which in our case is a table of 3000 numbers
In order to obtain the beam range, we call a function which calculates which position in the dose scorer binning
corresponds to the highest simulated dose.

In case you downloaded only this example file (`scripting_sh12a_run.py`), you need to install pymchelper package as well.
There are two possible ways of doing that::

Installing pymchelper package will all its extra features using::

 pip install "pymchelper[all]"

or installing pymchelper core package with additional scipy library::

 pip install pymchelper scipy

In case you cloned whole repository you can install pymchelper and its dependencies using::

 pip install requirements.txt

Finally simply execute::

 python scripting_sh12a_run.py

Note that SHIELD-HIT12A executable file is not provided with pymchelper and needs to be downloaded from shieldhit.org webpage
We assume that SHIELD-HIT12A is installed and `shieldhit` executable file is located in one of the directories
listed in the PATH environmental
"""

# import necessary packages from standard python library
import logging
import os
import shutil
import sys
import tempfile

# import numpy library with necessary functions needed to locate beam maximum 
import numpy as np
# import scipy library with necessary function to find the beam energy for which given range is achieved
from scipy.optimize import brentq

# import necessary objects from pymchelper library needed to run SHIELD-HIT12A simulation
from pymchelper.executor.options import SimulationSettings
from pymchelper.executor.runner import Runner

input_cfg_templ = {}
# dictionary holding filenames and contents of four main input files for SHIELD-HIT12A simulation
# the entry for beam.dat it not really a valid config, but a template with placeholder for incident particle energy
# the template can be instantiated into proper config using standar python operations on strings
# for example to set the primary particle energy to 100 MeV/n , first we make a fresh copy of the the template:
#
# input_cfg = input_cfg_templ.copy()
#
# then we overwrite the entry for beam.dat with the one with fixed energy:
#
# input_cfg['beam.dat'] = input_cfg['beam.dat'].format(energy=100.0)
#
# the reason we use the dictionary with strings is that is is easier to manipulate them than with the code
input_cfg_templ['beam.dat'] = """
RNDSEED      	89736501     ! Random seed
JPART0       	2            ! Incident particle type
TMAX0      	{energy:3.6f}   0.0  ! Incident energy; (MeV/nucl)
NSTAT           1000    -1 ! NSTAT, Step of saving
STRAGG          2            ! Straggling: 0-Off 1-Gauss, 2-Vavilov
MSCAT           2            ! Mult. scatt 0-Off 1-Gauss, 2-Moliere
NUCRE           0            ! Nucl.Reac. switcher: 1-ON, 0-OFF
""",
input_cfg_templ['mat.dat'] = """
MEDIUM 1
ICRU 276
END
""",
input_cfg_templ['detect.dat'] = """
Geometry Cyl
    Name MyCyl
        R 0.0 10.0 1
        Z 0.0 30.0 3000
""",
input_cfg_templ['detect.dat'] = """
*---><---><--------><------------------------------------------------>
    0    0           protons, H2O 30 cm cylinder, r=10, 1 zone
*---><---><--------><--------><--------><--------><--------><-------->
  RCC    1       0.0       0.0       0.0       0.0       0.0      30.0
                10.0
  RCC    2       0.0       0.0      -5.0       0.0       0.0      35.0
                15.0
  RCC    3       0.0       0.0     -10.0       0.0       0.0      40.0
                20.0
  END
  001          +1
  002          +2     -1
  003          +3     -2
  END
* material codes: 1 - liquid water (ICRU material no 276), 1000 - vacuum, 0 - black body
    1    2    3
    1 1000    0
"""


def run_sh12a(input_dict):
    """
    run_sh12a(input_dict)

    Run SHIELD-HIT12A simulation with given input configuration.
    The simulation results will be saved on disk in temporary location.
    Once simulation is completed the results will be extracted to a variable and temporary files will be removed.
    
    Parameters
    ----------
    input_dict : dict
        dictinary with contents of the SHIELD-HIT12A input files (beam.dat, geo.dat, mat.dat, detect.dat)
    Returns
    -------
    e : pymchelper.Estimator
        Estimator object containing along other things:
         - binning of the dose scorer along Z axis
         - simulated dose in each of the slab of the scoring cylinder
    """

    # create temporary directory to store simulation results
    temp_directory_path = tempfile.mkdtemp()

    # save the contents of the input dictionary into the files in temporary directory
    for config_filename in input_dict:
        absolute_path_temp_input_file = os.path.join(temp_directory_path, config_filename)
        with open(absolute_path_temp_input_file, 'w') as temp_input_file:
            temp_input_file.write(input_dict[config_filename])

    # `simulator_exec_path` can be set to absolute path to the SHIELD-HIT12A binary file,
    # here we set it to None to request pymchelper to look for it in PATH environmental variable
    simulator_exec_path=None

    # create pymchelper object which holds together all information needed to run the simulation
    opt = SimulationSettings(input_path=temp_directory_path,
                             simulator_exec_path=simulator_exec_path,  
                             cmdline_opts='-s')  #  additional option to avoid too much printout from SH12A

    # create runner object, needed to start simulation
    # we set jobs to `None`, so pymchelper will automatically detect how many parallel workers to run
    runner = Runner(jobs=None,  
                    settings=opt)

    # here simulation is started
    runner.run(output_directory=temp_directory_path)

    # read all the simulation output files
    data = runner.get_data(temp_directory_path)

    # remove temporary directory which includes simulation input and output files
    shutil.rmtree(temp_directory_path)

    # return an estimator corresponding to a 'mesh.bdo' output file
    return data['mesh']


def max_pos_at_energy(energy_MeV):
    """
    TODO
    """

    input_dict = input_cfg_templ
.copy()
    input_dict['beam.dat'] = input_dict['beam.dat'].format(energy=energy_MeV)
    data = run_sh12a(input_dict)
    index_of_max = np.argmax(data.pages[0].data[0, 0, :, 0, 0])
    max_pos_cm = data.z.data[index_of_max]
    print("Maximum position {:4.3f} cm at energy {:3.3f} MeV".format(max_pos_cm, energy_MeV))
    return max_pos_cm


def target_function(energy_MeV, pos_mm):
    """
    TODO
    """

    return max_pos_at_energy(energy_MeV) - pos_mm


def main(args=None):
    """
    Find such energy for which position of BP max is 20.05 mm
    :param args:
    :return:
    """
    if args is None:
        args = sys.argv[1:]
    pos_mm = 20.05
    brentq(target_function, a=20, b=400, args=(pos_mm,), xtol=0.01)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
