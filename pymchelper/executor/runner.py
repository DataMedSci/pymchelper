from copy import deepcopy
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import timeit
from multiprocessing import Pool

from enum import IntEnum
from typing import Tuple
from pymchelper.flair import Input
from pymchelper.executor.options import SimulationSettings

from pymchelper.simulator_type import SimulatorType
from pymchelper.readers.topas import get_topas_estimators
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

    def __init__(self,
                 settings: SimulationSettings,
                 jobs: int = None,
                 keep_workspace_after_run: bool = False,
                 output_directory: str = '.'):
        self.settings = settings

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

    def run(self):
        """
        Execute parallel simulation processes, creating workspace (and working directories) in the `output_directory`
        In case of successful execution return True, otherwise return False
        """
        start_time = timeit.default_timer()

        if self.settings.simulator_type in [SimulatorType.shieldhit, SimulatorType.fluka]:
            # SHIELD-HIT12A and Fluka require RNG seeds to be integers greater or equal to 1
            # each of the workers needs to have its own different RNG seed
            rng_seeds = range(1, self.jobs + 1)

        elif self.settings.simulator_type == SimulatorType.topas:
            # For TOPAS we don't need to create multiple working directories and a pool of workers,
            # as we can use embedded parallelization in TOPAS.
            # For that we need to modify the input file and set the number of threads to the number of jobs.
            # We set one rng seed, so one working directory and one worker will be created.

            modified_input_filename = Path(self.settings.input_path).name.replace(".txt", "_modified.txt")
            modified_input_path = Path(self.settings.input_path).parent / modified_input_filename

            with open(self.settings.input_path, 'r') as f:
                config = f.read()
                if "i:Ts/NumberOfThreads" in config:
                    pattern = r"i:Ts/NumberOfThreads\s*=\s*\d+"
                    replacement = f"i:Ts/NumberOfThreads = {self.jobs}"
                    config = re.sub(pattern, replacement, config)
                else:
                    config = f"i:Ts/NumberOfThreads = {self.jobs}\n" + config

            modified_input_path.write_text(config)

            self.settings.input_path = str(modified_input_path)

            rng_seeds = [1]

        # create working directories
        self.workspace_manager.create_working_directories(simulation_input_path=self.settings.input_path,
                                                          rng_seeds=rng_seeds)

        if self.settings.simulator_type == SimulatorType.fluka:
            for seed, workdir in zip(rng_seeds, self.workspace_manager.working_directories_abs_paths):
                destination = str(Path(workdir) / Path(self.settings.input_path).name)
                self.__update_fluka_input_file(destination, seed)

        # rng seeds injection to settings for each SingleSimulationExecutor call
        # TODO consider better way of doing it  # skipcq: PYL-W0511
        settings_list = []
        for rng_seed in rng_seeds:
            current_settings = deepcopy(self.settings)  # do not modify original arguments
            if self.settings.simulator_type in [SimulatorType.shieldhit, SimulatorType.topas]:
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

        # scans output directory for MC simulation output files
        estimators_dict = {}
        estimators_list = []

        if self.settings.simulator_type == SimulatorType.shieldhit:
            output_files_pattern = str(Path(self.workspace_manager.output_dir_absolute_path) / "run_*" / "*.bdo")
            logging.debug("Files to merge %s", output_files_pattern)
            # convert output files to list of estimator objects
            estimators_list = frompattern(output_files_pattern)

        elif self.settings.simulator_type == SimulatorType.topas:
            output_files_path = str(Path(self.workspace_manager.output_dir_absolute_path) / "run_1")
            estimators_list = get_topas_estimators(output_files_path)

        elif self.settings.simulator_type == SimulatorType.fluka:
            output_files_pattern = os.path.join(self.workspace_manager.output_dir_absolute_path, "run_*", "*_fort.*")
            logging.debug("Files to merge %s", output_files_pattern)
            estimators_list = frompattern(output_files_pattern)

        for estimator in estimators_list:
            logging.debug("Appending estimator for {:s}".format(estimator.file_corename))
            estimators_dict[estimator.file_corename] = estimator
        elapsed = timeit.default_timer() - start_time
        logging.info("Workspace reading {:.3f} seconds".format(elapsed))

        return estimators_dict

    def clean(self):
        """Removes all working directories (if exists)"""
        self.workspace_manager.clean()

    @staticmethod
    def __update_fluka_input_file(destination: str, rng_seed: int):
        """Updates the FLUKA input file with the new RNG seed."""
        with open(destination, 'r') as destination_file:
            lines = destination_file.readlines()
        has_randomize_card = False
        for index, line in enumerate(lines):
            if line.startswith('RANDOMIZ'):
                card = Input.Card("RANDOMIZ")
                card.setWhat(1, 1.)
                card.setWhat(2, rng_seed)
                lines[index] = card.toStr() + '\n'
                has_randomize_card = True
        if not has_randomize_card:
            card = Input.Card("RANDOMIZ")
            card.setWhat(1, 1.)
            card.setWhat(2, rng_seed)
            lines.append(card.toStr() + '\n')

        with open(destination, 'w') as destination_file:
            destination_file.writelines(lines)


class SingleSimulationExecutor:
    """
    Callable class responsible for execution of the single MC simulation process.
    """

    def __call__(self, settings_and_working_dir: Tuple[SimulationSettings, str], **kwargs):

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
            if settings.simulator_type == SimulatorType.fluka:
                input_file_path = str(Path(working_dir_abs_path) / Path(settings.input_path).name)
                command_as_list.append(input_file_path)
            else:
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
