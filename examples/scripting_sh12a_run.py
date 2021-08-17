import logging
import os
import sys
import tempfile
import shutil

import numpy as np

from pymchelper.executor.options import MCOptions
from pymchelper.executor.runner import Runner


input_cfg = {
    'beam.dat': """
RNDSEED      	89736501     ! Random seed
JPART0       	2           ! Incident particle type
TMAX0      	{energy:3.6f}   0.0  ! Incident energy; (MeV/nucl)
NSTAT           1000    -1 ! NSTAT, Step of saving
STRAGG          2            ! Straggling: 0-Off 1-Gauss, 2-Vavilov
MSCAT           2            ! Mult. scatt 0-Off 1-Gauss, 2-Moliere
NUCRE           0            ! Nucl.Reac. switcher: 1-ON, 0-OFF
""",
    'mat.dat': """
MEDIUM 1
ICRU 276
END
""",
    'detect.dat': """
*----0---><----1---><----2---><----3---><----4---><----5---><----6--->
MSH             -5.0      -5.0       0.0       5.0       5.0      30.0
                   1         1      1000        -1    ENERGY   ex_zmsh
""",
    'geo.dat': """
*---><---><--------><------------------------------------------------>
    0    0           C12 200 MeV/A, H2O 30 cm cylinder, r=10, 1 zone
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
    1    2    3
    1 1000    0
"""}


def run_sh12a(input_dict):
    dirpath = tempfile.mkdtemp()

    for config_file in input_dict:
        file_path = os.path.join(dirpath, config_file)
        with open(file_path, 'w') as output_file:
            output_file.write(input_dict[config_file])

    opt = MCOptions(input_path=dirpath,
                    executable_path=None,
                    user_opt='-s')

    r = Runner(jobs=1, options=opt)
    r.run(outdir=dirpath)
    data = r.get_data(dirpath)
    shutil.rmtree(dirpath)
    return data['ex_zmsh']


def max_pos_at_energy(energy_MeV):
    input_dict = input_cfg.copy()
    input_dict['beam.dat'] = input_dict['beam.dat'].format(energy=energy_MeV)
    data = run_sh12a(input_dict)
    index_of_max = np.argmax(data.pages[0].data[0, 0, :, 0, 0])
    max_pos_cm = data.z.data[index_of_max]
    print("Maximum position {:4.3f} cm at energy {:3.3f} MeV".format(max_pos_cm, energy_MeV))
    return max_pos_cm


def target_function(energy_MeV, pos_mm):
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
    try:
        from scipy.optimize import brentq
        brentq(target_function, a=20, b=400, args=(pos_mm,), xtol=0.01)
    except ImportError:
        logging.error("scipy not installed, output won't be generated")
        return None


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
