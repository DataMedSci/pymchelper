import logging
import glob
import os
import shutil
import subprocess
from enum import IntEnum
from multiprocessing import Pool
from pymchelper.io import frompattern


class MCOutType(IntEnum):
    raw = 0
    plot = 1
    txt = 2


class FlukaEnviroment:
    executable_file = 'rfluka'


class SH12AEnviroment:
    executable_file = 'shieldhit'


class KeyboardInterruptError(Exception):
    pass


class Runner:
    def __init__(self, jobs=None, options=None):
        self.options = options
        self.pool = Pool(processes=jobs)
        self.jobs = self.pool._processes  # always int

    def run(self, outdir):
        rng_seeds = range(1, self.jobs + 1)
        e = Executor(outdir=outdir, options=self.options)
        res = None
        try:
            res = self.pool.map(e, rng_seeds)
        except KeyboardInterrupt:
            logging.info('got ^C while pool mapping, terminating the pool')
            self.pool.terminate()
            logging.info('pool is terminated')
        except Exception as e:
            logging.info('got exception: %r, terminating the pool' % (e,))
            self.pool.terminate()
            logging.info('pool is terminated')

            logging.info(res)
        return res

    def get_data(self, workspaces):
        if not workspaces:
            return None
        total_results = {}

        full_list = []
        for d in workspaces:
            tmp_list = sorted(glob.glob(os.path.join(d, "*.bdo")))
            full_list += tmp_list

        dets = frompattern(full_list)
        for det in dets:
            total_results[det.corename] = det

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
        try:
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
            logging.debug('dir {:s}, cmd {:s}'.format(workspace, str(current_options)))

            DEVNULL = open(os.devnull, 'wb')
            subprocess.check_call(str(current_options).split(), cwd=workspace, stdout=DEVNULL, stderr=DEVNULL)
        except KeyboardInterrupt:
            raise KeyboardInterruptError()

        return workspace
