from copy import deepcopy
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


class Runner:
    """
    Main class responsible for configuring and starting multiple parallel MC simulation processes
    It can be used to access combined averaged results of the simulation.
    """
    def __init__(self, jobs=None, keep_workspace_after_run=False, output_directory='.'):

        # create pool of processes, waiting to be started by run method
        # if jobs is not specified, os.cpu_count() would be used
        self._pool = Pool(processes=jobs)

        # User of the runner has two options: either to specify number of parallel jobs by
        # setting the self.jobs to given number, or to leave it as None. If self.jobs is None
        # then multiprocessing library will automatically allocate number of parallel jobs to `os.cpu_count()`
        # Therefore we cannot rely of self.jobs as the actual counter of parallel processes
        # Instead we use undocumented feature of multiprocessing module,
        # extracting actual number of allocated processes from `_processes` attribute in Pool class
        # To see how it is used internally in the Python (in v3.9) source code take a look at:
        # https://github.com/python/cpython/blob/3.9/Lib/multiprocessing/pool.py#L210
        self.jobs = self._pool._processes

        # workspace is a collection of working directories
        # this manager is responsible for creating and cleaning working directories
        self.workspace_manager = WorkspaceManager(output_directory=output_directory,
                                                  keep_workspace_after_run=keep_workspace_after_run)

    def run(self, settings):
        """
        Execute parallel simulation processes, creating workspace (and working directories) in the `output_directory`
        In case of successful execution return True, otherwise return False
        """
        start_time = timeit.default_timer()

        # SHIELD-HIT12A and Fluka require RNG seeds to be integers greater or equal to 1
        # each of the workers needs to have its own different RNG seed
        rng_seeds = range(1, self.jobs + 1)

        # create working directories
        self.workspace_manager.create_working_directories(simulation_input_path=settings.input_path,
                                                          rng_seeds=rng_seeds)

        # rng seeds injection to settings for each SingleSimulationExecutor call
        # TODO consider better way of doing it  # skipcq: PYL-W0511
        settings_list = []
        for rng_seed in rng_seeds:
            current_settings = deepcopy(settings)  # do not modify original arguments
            current_settings.set_rng_seed(rng_seed)
            settings_list.append(current_settings)

        # create executor callable object for current run
        executor = SingleSimulationExecutor()

        try:
            # start execution using pool of workers, mapping the executor callable object to the different settings
            # and workspaces
            self._pool.map(executor, zip(settings_list, self.workspace_manager.working_directories_abs_paths))
        except KeyboardInterrupt:
            logging.info('Terminating the pool')
            self._pool.terminate()
            logging.info('Pool is terminated')
            self.workspace_manager.clean()
            return False

        elapsed = timeit.default_timer() - start_time
        logging.info("run elapsed time {:.3f} seconds".format(elapsed))
        return True

    def get_data(self):
        """
        Scans the output directory for location of the working directories (like run_1, run_2).
        Takes all files from all working directories in `output_dir`,
        merges their content to form pymchelper Estimator objects.
        For each of the output file a single Estimator objects is created, which holds numpy arrays with results.
        Return dictionary with keys being output filenames, and values being Estimator objects
        """
        start_time = timeit.default_timer()

        # TODO line below is specific to SHIELD-HIT12A, should be generalised  # skipcq: PYL-W0511
        # scans output directory for MC simulation output files
        output_files_pattern = os.path.join(self.workspace_manager.output_dir_absolute_path, "run_*", "*.bdo")
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

    def clean(self):
        """
        Removes all working directories (if exists)
        """
        self.workspace_manager.clean()


class SingleSimulationExecutor:
    """
    Callable class responsible for execution of the single MC simulation process.
    """

    def __call__(self, settings_and_working_dir, **kwargs):

        # we deliberately combine settings and list of working directories
        # in the single argument `settings_and_working_dir`
        # as this would simplify using this class by multiprocessing module
        settings, working_dir_abs_path = settings_and_working_dir
        try:
            # combine MC engine executable with its command line options to form core of the command string
            # this will form basis of the command, like:
            # /usr/local/bin/shieldhit --time 00:30:50 -v -N 3
            core_command_string = str(settings)

            # for easier digesting by subprocess module, convert command string to a list
            # and finally append the location of the input files
            # finally we obtain a list like:
            # ('/usr/local/bin/shieldhit', '--time', '00:30:50', '-v', '-N', '3', '/data/my/simulation/input')
            command_as_list = core_command_string.split()
            command_as_list.append(working_dir_abs_path)

            # execute the MC simulation on a spawned process
            # TODO handle this differently, i.e. redirect it to file or save in some variable   # skipcq: PYL-W0511
            logging.debug('working directory {:s}, command {:s}'.format(working_dir_abs_path,
                                                                        ' '.join(command_as_list)))
            DEVNULL = open(os.devnull, 'wb')
            subprocess.check_call(command_as_list, cwd=working_dir_abs_path, stdout=DEVNULL, stderr=DEVNULL)
        except KeyboardInterrupt:
            logging.debug("KeyboardInterrupt")
            raise KeyboardInterrupt


class WorkspaceManager:
    """
    A workspace consists of multiple working directories (i.e. run_1, run_2),
    each per one of the parallel simulation run.
    """
    def __init__(self, output_directory='.', keep_workspace_after_run=False):
        self.output_dir_absolute_path = os.path.abspath(output_directory)
        self.keep_workspace_after_run = keep_workspace_after_run
        self.working_directories_abs_paths = []

    def create_working_directories(self, simulation_input_path, rng_seeds=()):
        """
        Create working directories and fill `self.working_directories_abs_paths`
        """
        self.working_directories_abs_paths = []
        for rng_seed in rng_seeds:
            # set workspace to a subdirectory of the output_directory, with run_* pattern
            # i.e. /home/user/output/run_3
            working_dir_abs_path = os.path.join(self.output_dir_absolute_path, 'run_{:d}'.format(rng_seed))
            logging.info("Workspace {:s}".format(working_dir_abs_path))

            if os.path.isdir(simulation_input_path):
                # if path already exists, remove it before copying with copytree()
                if os.path.exists(working_dir_abs_path):
                    shutil.rmtree(working_dir_abs_path)
                # if cleaned or not existing, then create it
                if not os.path.exists(working_dir_abs_path):
                    os.makedirs(working_dir_abs_path)
                # copy all files from the directory
                for directory_entry in os.listdir(simulation_input_path):
                    path_to_directory_entry = os.path.join(simulation_input_path, directory_entry)
                    if os.path.isfile(path_to_directory_entry):
                        shutil.copy2(path_to_directory_entry, working_dir_abs_path)
                logging.debug("Copying input files into {:s}".format(working_dir_abs_path))
            elif os.path.isfile(simulation_input_path):
                if not os.path.exists(working_dir_abs_path):
                    os.makedirs(working_dir_abs_path)
                shutil.copy2(simulation_input_path, working_dir_abs_path)
                logging.debug("Copying input files into {:s}".format(working_dir_abs_path))
            else:
                logging.debug("Input files {:s} not a dir or file".format(simulation_input_path))

            self.working_directories_abs_paths.append(working_dir_abs_path)

    def clean(self):
        """
        clean the workspace by removing all working directories
        (only if requested by `keep_workspace_after_run` flag)
        """
        if not self.keep_workspace_after_run:
            start_time = timeit.default_timer()
            for working_dir_abs_path in self.working_directories_abs_paths:
                # shutil.rmtree will throw exception if the directory we are trying to remove doesn't exist
                # hence we only remove existing directories
                # this allows safely to call `clean` method multiple times
                if os.path.exists(working_dir_abs_path):
                    shutil.rmtree(working_dir_abs_path)
            elapsed = timeit.default_timer() - start_time
            print("Cleaning {:.3f} seconds".format(elapsed))
