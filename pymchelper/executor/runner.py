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
    def __init__(self, jobs=None, keep_flag=False, output_directory='.'):

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

        self.dir_manager = DirectoryManager(output_directory=output_directory, keep_flag=keep_flag)

    def run(self, settings):
        """
        Execute parallel simulation, creating temporary workspace in the `output_directory`
        In case of successful execution return list of directories with results, otherwise return None
        """
        start_time = timeit.default_timer()

        # SHIELD-HIT12A and Fluka require RNG seeds to be integers greater or equal to 1
        # each of the workers needs to have its own different RNG seed
        rng_seeds = range(1, self.jobs + 1)

        # create workspaces
        workspaces = self.dir_manager.new_workspaces(input_path=settings.input_path, rng_seeds=rng_seeds)

        # temporary rework of rng_seeds injection to settings (formerly executor was responsible for it)
        # TODO rework it somehow   # skipcq: PYL-W0511
        settings_list = []
        for rng_seed in rng_seeds:
            current_settings = settings
            current_settings.set_rng_seed(rng_seed)
            settings_list.append(current_settings)

        # create executor callable object for current run
        executor = Executor()

        try:
            # start execution using pool of workers, mapping the executor callable object to the different settings
            # and workspaces
            self._pool.map(executor, zip(settings_list, workspaces))
        except KeyboardInterrupt:
            logging.info('Terminating the pool')
            self._pool.terminate()
            logging.info('Pool is terminated')
            self.dir_manager.clean()
            return False

        elapsed = timeit.default_timer() - start_time
        logging.info("run elapsed time {:.3f} seconds".format(elapsed))
        return True

    def get_data(self):
        """
        Scans output directory for location of the workspaces (directories like run_1, run_2).
        Takes all files from all workspace in `output_dir`, merges their content to form pymchelper Estimator objects.
        For each of the output file a single Estimator objects is created, which holds numpy arrays with results.
        Return dictionary with keys being output filenames, and values being Estimator objects
        # TODO consider replace output_dir with list of workspace   # skipcq: PYL-W0511
        """
        if not self.dir_manager.output_directory:
            return None
        start_time = timeit.default_timer()

        # TODO line below is specific to SHIELD-HIT12A, should be generalised  # skipcq: PYL-W0511
        # scans output directory for MC simulation output files
        output_files_pattern = os.path.join(self.dir_manager.output_directory, "run_*", "*.bdo")
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
        self.dir_manager.clean(reset=False)


class Executor:
    """
    Callable class responsible for execution of single MC simulation process.
    """

    def __call__(self, settings_and_workspace, **kwargs):

        settings, workspace = settings_and_workspace
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
            command_as_list.append(workspace)

            # execute the MC simulation on a spawned process
            # TODO handle this differently, i.e. redirect it to file or save in some variable   # skipcq: PYL-W0511
            logging.debug('working directory {:s}, command {:s}'.format(workspace, ' '.join(command_as_list)))
            DEVNULL = open(os.devnull, 'wb')
            subprocess.check_call(command_as_list, cwd=workspace, stdout=DEVNULL, stderr=DEVNULL)
        except KeyboardInterrupt:
            logging.debug("KeyboardInterrupt")
            raise KeyboardInterrupt


class DirectoryManager:
    """
    DirectoryManager
    """
    def __init__(self, output_directory='.', keep_flag=False):
        self.output_directory = os.path.abspath(output_directory)
        self.keep_flag = keep_flag
        self.workspaces = []

    def new_workspaces(self, input_path=None, rng_seeds=tuple()):
        """
        prepare workspaces
        """
        self.clean(reset=True)
        if input_path:
            for rng_seed in rng_seeds:
                # set workspace to a subdirectory of the output_directory, with run_* pattern
                # i.e. /home/user/output/run_3
                workspace = os.path.join(self.output_directory, 'run_{:d}'.format(rng_seed))
                logging.info("Workspace {:s}".format(workspace))

                if os.path.isdir(input_path):
                    # if path already exists, remove it before copying with copytree()
                    if os.path.exists(workspace):
                        shutil.rmtree(workspace)
                    shutil.copytree(input_path, workspace)
                    logging.debug("Copying input files into {:s}".format(workspace))
                elif os.path.isfile(input_path):
                    if not os.path.exists(workspace):
                        os.makedirs(workspace)
                    shutil.copy2(input_path, workspace)
                    logging.debug("Copying input files into {:s}".format(workspace))
                else:
                    logging.debug("Input files {:s} not a dir or file".format(input_path))

                self.workspaces.append(workspace)
        return self.workspaces

    def clean(self, reset=False):
        """
        clean the directory only if keep_flag == False or reset is requested
        """
        if not self.keep_flag or reset:
            start_time = timeit.default_timer()
            for workspace in self.workspaces:
                shutil.rmtree(workspace)
            elapsed = timeit.default_timer() - start_time
            print("Cleaning {:.3f} seconds".format(elapsed))
