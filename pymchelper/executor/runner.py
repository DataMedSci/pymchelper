import logging
import os
import shutil
import subprocess
import timeit
from multiprocessing import Pool

from enum import IntEnum

from pymchelper.input_output import frompattern


class OutputDataType(IntEnum):
    """
    Output type requested by user plots (i.e .png) or text data
    """
    plot = 1
    txt = 2


class KeyboardInterruptError(Exception):
    """
    Useful to handle process interruption via Ctrl-C
    TODO consider simplifying try/catch ladder
    """


class Runner:
    """
    Main class responsible for configuring and starting multiple parallel MC simulation processes
    It can be used to access combined averaged results of the simulation.
    """
    def __init__(self, jobs=None, settings=None):
        # object of SimulationSettings class
        self.settings = settings

        # create pool of processes, waiting to be started by run method
        # if jobs is not specified, os.cpu_count() would be used
        self._pool = Pool(processes=jobs)

        # self.jobs will be either a value provided by user
        # or actual number of allocated processes, if `jobs` were set to None
        # TODO check if `_pool._processes` is valid construct  # skipcq: PYL-W0511
        self.jobs = self._pool._processes

    def run(self, output_directory):
        """
        Execute parallel simulation, creating temporary workspace in the `output_directory`
        In case of successful execution return list of directories with results, otherwise return None
        """
        start_time = timeit.default_timer()

        # SHIELD-HIT12A and Fluka require RNG seeds to be integers greater or equal to 1
        # each of the workers needs to have its own different RNG seed
        rng_seeds = range(1, self.jobs + 1)

        # create executor callable object for current run
        executor = Executor(output_directory=output_directory, settings=self.settings)

        # start execution using pool of workers, mapping the executor callable object to the different RNG seeds
        # each of executor will return upon success path to a working directory with results
        # pool of processes would gather these paths in a combined list
        result_directories = None
        try:
            result_directories = self._pool.map(executor, rng_seeds)
        except KeyboardInterrupt:
            logging.info('got ^C while pool mapping, terminating the pool')
            self._pool.terminate()
            logging.info('pool is terminated')
        elapsed = timeit.default_timer() - start_time
        logging.info("run elapsed time {:.3f} seconds".format(elapsed))
        return result_directories

    @staticmethod
    def get_data(output_dir):
        """
        Scans output directory for location of the workspaces (directories like run_1, run_2).
        Takes all files from all workspace in `output_dir`, merges their content to form pymchelper Estimator objects.
        For each of the output file a single Estimator objects is created, which holds numpy arrays with results.
        Return dictionary with keys being output filenames, and values being Estimator objects
        # TODO consider replace output_dir with list of workspace
        """
        if not output_dir:
            return None
        start_time = timeit.default_timer()

        # TODO line below is specific to SHIELD-HIT12A, should be generalised  # skipcq: PYL-W0511
        # scans output directory for MC simulation output files
        output_files_pattern = os.path.join(output_dir, "run_*", "*.bdo")
        logging.debug("Files to merge {:s}".format(output_files_pattern))

        estimators_dict = {}
        # convert output files to list of estimator objects
        estimators_list = frompattern(output_files_pattern)
        for estimator in estimators_list:
            logging.debug("Appending estimator for {:s}".format(estimator.file_corename))
            estimators_dict[estimator.file_corename] = estimator
        elapsed = timeit.default_timer() - start_time
        logging.info("Workspace reading {:.3f} seconds".format(elapsed))

        return estimators_dict

    @staticmethod
    def clean(directories_list):
        """
        Remove each directory from given list.
        Useful to remove all workspace directories (run_1, run_2,...)
        """
        for directory in directories_list:
            shutil.rmtree(directory)


class Executor:
    """
    Callable class responsible for execution of single MC simulation process.
    """
    def __init__(self, output_directory, settings):
        self.output_directory = os.path.abspath(output_directory)
        self.settings = settings

    def __call__(self, rng_seed, **kwargs):

        # set workspace to a subdirectory of the output_directory, with run_* pattern
        # i.e. /home/user/output/run_3
        workspace = os.path.join(self.output_directory, 'run_{:d}'.format(rng_seed))

        logging.info("Workspace {:s}".format(workspace))
        try:
            # copy simulation input files into the workspace directory
            # TODO extract this step into separate method  # skipcq: PYL-W0511
            if os.path.isdir(self.settings.input_path):
                # if path already exists, remove it before copying with copytree()
                if os.path.exists(workspace):
                    shutil.rmtree(workspace)
                shutil.copytree(self.settings.input_path, workspace)
                logging.debug("Copying input files into {:s}".format(workspace))
            elif os.path.isfile(self.settings.input_path):
                if not os.path.exists(workspace):
                    os.makedirs(workspace)
                shutil.copy2(self.settings.input_path, workspace)
                logging.debug("Copying input files into {:s}".format(workspace))
            else:
                logging.debug("Input files {:s} not a dir or file".format(self.settings.input_path))

            # now we proceed to construction of the command which will execute MC engine
            # the command usually consists of simulator executable path, followed by command line options
            # and finally a location of the input file, for example
            # /usr/local/bin/shieldhit --time 00:30:50 -v -N 3 /data/my/simulation/input

            # adjust setting for this particular run with RNG seed being set
            current_options = self.settings
            current_options.set_rng_seed(rng_seed)

            # combine MC engine executable with its command line options to form core of the command string
            # this will form basis of the command, like:
            # /usr/local/bin/shieldhit --time 00:30:50 -v -N 3
            core_command_string = str(current_options)

            # for easier digesting by subprocess module, convert command string to a list
            # and finally append the location of the input files
            # finally we obtain a list like:
            # ('/usr/local/bin/shieldhit', '--time', '00:30:50', '-v', '-N', '3', '/data/my/simulation/input')
            command_as_list = core_command_string.split()
            command_as_list.append(workspace)

            # execute the MC simulation on a spawned process
            # TODO handle this differently, i.e. redirect it to file or save in some variable   # skipcq: PYL-W0511
            logging.debug('working directory {:s}, command {:s}'.format(workspace, ' '.join(command_as_list)))
            DEVNULL = open(os.devnull, 'wb')
            subprocess.check_call(command_as_list, cwd=workspace, stdout=DEVNULL, stderr=DEVNULL)

        # in case of Ctrl-C
        except KeyboardInterrupt:
            logging.debug("KeyboardInterrupt")
            raise KeyboardInterruptError()

        return workspace
