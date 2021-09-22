import logging
import os
import shutil
import subprocess
import timeit
from enum import IntEnum
from multiprocessing import Pool
from pymchelper.input_output import frompattern


class MCOutType(IntEnum):
    """
    Output type requested by user (raw files, i.e. bdo) or plots (i.e .png) or text data
    """
    raw = 0
    plot = 1
    txt = 2


class KeyboardInterruptError(Exception):
    """
    TODO
    """


class Runner:
    """
    TODO
    """
    def __init__(self, jobs=None, options=None):
        self.options = options
        self.pool = Pool(processes=jobs)
        self.jobs = self.pool._processes  # always int

    def run(self, outdir):
        """
        TODO
        """
        start_time = timeit.default_timer()
        rng_seeds = range(1, self.jobs + 1)
        e = Executor(outdir=outdir, options=self.options)
        res = None
        try:
            res = self.pool.map(e, rng_seeds)
        except KeyboardInterrupt:
            logging.info('got ^C while pool mapping, terminating the pool')
            self.pool.terminate()
            logging.info('pool is terminated')

            logging.info(res)
            shutil.rmtree(outdir)
        elapsed = timeit.default_timer() - start_time
        print("elapsed time {:.3f} seconds".format(elapsed))
        return res

    @staticmethod
    def get_data(output_dir):
        """
        TODO
        """
        if not output_dir:
            return None
        start_time = timeit.default_timer()
        total_results = {}

        output_files_pattern = os.path.join(output_dir, "*", "*.bdo")
        logging.debug("Files to merge {:s}".format(output_files_pattern))

        estimators = frompattern(output_files_pattern)
        for est in estimators:
            logging.debug("Appending estimator for {:s}".format(est.file_corename))
            total_results[est.file_corename] = est
        elapsed = timeit.default_timer() - start_time
        logging.info("Workspace reading {:.3f} seconds".format(elapsed))

        return total_results

    @staticmethod
    def clean(workspaces):
        """
        TODO
        """
        for w in workspaces:
            shutil.rmtree(w)


class Executor:
    """
    TODO
    """
    def __init__(self, outdir, options):
        self.outdir = os.path.abspath(outdir)
        self.options = options

    def __call__(self, rng_seed, **kwargs):
        workspace = os.path.join(self.outdir, 'run_{:d}'.format(rng_seed))
        logging.info("Workspace {:s}".format(workspace))
        try:
            if os.path.isdir(self.options.input_path):
                # if path already exists, remove it before copying with copytree()
                if os.path.exists(workspace):
                    shutil.rmtree(workspace)
                shutil.copytree(self.options.input_path, workspace)
                logging.debug("Copying input files into {:s}".format(workspace))
            elif os.path.isfile(self.options.input_path):
                if not os.path.exists(workspace):
                    os.makedirs(workspace)
                shutil.copy2(self.options.input_path, workspace)
                logging.debug("Copying input files into {:s}".format(workspace))
            else:
                logging.debug("Input files {:s} not a dir or file".format(self.options.input_path))
            current_options = self.options
            current_options.set_rng_seed(rng_seed)
            current_options.workspace = workspace
            logging.debug('dir {:s}, cmd {:s}'.format(workspace, str(current_options)))

            # handle standard output differently, i.e. redirect it to some file or save in some variable
            DEVNULL = open(os.devnull, 'wb')
            subprocess.check_call(str(current_options).split(), cwd=workspace, stdout=DEVNULL, stderr=DEVNULL)
        except KeyboardInterrupt:
            logging.debug("KeyboardInterrupt")
            raise KeyboardInterruptError()

        return workspace
