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
JPART0       	25           ! Incident particle type
HIPROJ     	12.0    6.0  ! A and Z of heavy ion
TMAX0      	391.0   0.0  ! Incident energy; (MeV/nucl)
NSTAT           500    500 ! NSTAT, Step of saving
STRAGG          2            ! Straggling: 0-Off 1-Gauss, 2-Vavilov
MSCAT           2            ! Mult. scatt 0-Off 1-Gauss, 2-Moliere
NUCRE           1            ! Nucl.Reac. switcher: 1-ON, 0-OFF
""",
    'mat.dat': """
MEDIUM 1
ICRU 276
END
""",
    'detect.dat': """
*----0---><----1---><----2---><----3---><----4---><----5---><----6--->
MSH             -5.0      -5.0       0.0       5.0       5.0      30.0
                   1         1       300        -1    ENERGY   ex_zmsh
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


def run_sh12a():
    dirpath = tempfile.mkdtemp()

    for config_file in input_cfg:
        file_path = os.path.join(dirpath, config_file)
        with open(file_path, 'w') as f:
            f.write(input_cfg[config_file])

    opt = MCOptions(input_cfg=dirpath,
                    executable_path=None,
                    user_opt='-s')

    r = Runner(jobs=None, options=opt)
    workspaces = r.run(outdir=dirpath)
    data = r.get_data(workspaces)
    shutil.rmtree(dirpath)
    return data['ex_zmsh']


def analyze(data):
    index_of_max = np.argmax(data.v)
    max_pos_cm = list(data.z)[index_of_max]
    print("Maximum position {:4.3} cm".format(max_pos_cm))


def main(args=sys.argv[1:]):
    data = run_sh12a()
    analyze(data)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
