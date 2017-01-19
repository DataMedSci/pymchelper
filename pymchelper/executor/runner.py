import os
import logging
import shutil
import subprocess
from enum import IntEnum
from multiprocessing import Pool
import numpy as np

logger = logging.getLogger(__name__)


class MCOutType(IntEnum):
    raw = 0
    plot = 1
    txt = 2


class FlukaEnviroment:
    executable_file = 'rfluka'


class SH12AEnviroment:
    executable_file = 'shieldhit'


#
# def gcd(a, b):
#     if a%b == 0:
#         return b
#     return gcd(b, a%b)


class Runner:
    def __init__(self, jobs=None, options=None):
        self.options = options
        self.pool = Pool(processes=jobs)
        self.jobs = self.pool._processes  # always int

    def run(self, outdir):
        rng_seeds = range(1, self.jobs + 1)
        e = Executor(outdir=outdir, options=self.options)
        res = self.pool.map(e, rng_seeds)
        logger.info(res)
        return res

    def get_data(self, workspaces):
        import glob
        from pymchelper.detector import Detector
        total_results = {}
        for d in workspaces:
            files = sorted(glob.glob("{:s}/*.bdo".format(d)))
            for item in files:
                key = os.path.basename(item)[:-8]
                value = Detector()
                value.read(item)
                if key not in total_results:
                    total_results[key] = value
                    total_results[key]._M2 = np.zeros_like(value.data)
                    total_results[key].error = np.zeros_like(value.data)
                else:
                    total_results[key].average_with_other(value)

        for k in total_results:
            total_results[k].error /= np.sqrt(total_results[k].counter)

        return total_results

    def clean(self, workspaces):
        for w in workspaces:
            shutil.rmtree(w)


class Executor:
    def __init__(self, outdir, options):
        self.outdir = os.path.abspath(outdir)
        self.options = options

    def __call__(self, rng_seed, **kwargs):
        workspace = os.path.join(self.outdir, 'run_{:d}'.format(rng_seed))
        if os.path.isdir(self.options.input_cfg):
            # if path already exists, remove it before copying with copytree()
            if os.path.exists(workspace):
                shutil.rmtree(workspace)
            shutil.copytree(self.options.input_cfg, workspace)
        elif os.path.isfile(self.options.input_cfg):
            if not os.path.exists(workspace):
                os.makedirs(workspace)
            shutil.copy2(self.options.input_cfg, workspace)
        current_options = self.options
        current_options.set_rng_seed(rng_seed)
        current_options.workspace = workspace
        logger.debug('dir {:s}, cmd {:s}'.format(workspace, str(current_options)))

        DEVNULL = open(os.devnull, 'wb')
        subprocess.check_call(str(current_options).split(), cwd=workspace, stdout=DEVNULL, stderr=DEVNULL)

        return workspace
