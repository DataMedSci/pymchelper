from copy import deepcopy
from glob import glob
import logging
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import timeit
from multiprocessing import Pool

from enum import IntEnum
from typing import List, Tuple
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

        # if jobs is not specified, use the same default as multiprocessing.Pool:
        # the number of CPUs this process may use (Python >= 3.13), otherwise the number of CPUs
        if jobs is None:
            if hasattr(os, "process_cpu_count"):
                jobs = os.process_cpu_count()
            else:
                jobs = os.cpu_count()
        self.jobs = jobs

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

        if self.settings.simulator_type == SimulatorType.topas:
            # For TOPAS we don't need to create multiple working directories and a pool of workers,
            # as we can use embedded parallelization in TOPAS: one working directory, one process,
            # and the number of threads in the input file set to the number of jobs.
            job_numbers = [1]
        else:
            job_numbers = list(range(1, self.jobs + 1))

        # create working directories, each with its own copy of the input files
        self.workspace_manager.create_working_directories(simulation_input_path=self.settings.input_path,
                                                          job_numbers=job_numbers)

        # each job gets its own RNG seed: the seed given by the user (0 if none) plus the job number,
        # so jobs differ from each other and runs with different user seeds differ from each other
        commands_and_working_dirs = []
        for job_number, working_dir in zip(job_numbers, self.workspace_manager.working_directories_abs_paths):

            if self.settings.simulator_type == SimulatorType.shieldhit:
                job_settings = deepcopy(self.settings)  # do not modify original arguments
                job_settings.set_rng_seed(self.settings.get_rng_seed() + job_number)
                command = job_settings.command_as_list()
                command.append(working_dir)

            elif self.settings.simulator_type == SimulatorType.fluka:
                input_file_copy = str(Path(working_dir) / Path(self.settings.input_path).name)
                user_seed = self._read_fluka_rng_seed(self.settings.input_path)
                self.__update_fluka_input_file(input_file_copy, user_seed + job_number)
                command = self.settings.command_as_list()
                command.append(input_file_copy)

            elif self.settings.simulator_type == SimulatorType.topas:
                # TOPAS takes the parameter file as its first argument, and the seed from i:Ts/Seed in that file
                input_file_copy = Path(working_dir) / Path(self.settings.input_path).name
                self._set_topas_number_of_threads(input_file_copy, self.jobs)
                command = [os.path.abspath(self.settings.executable_path), input_file_copy.name]

            commands_and_working_dirs.append((command, working_dir))

        # create executor callable object for current run
        executor = SingleSimulationExecutor()

        try:
            # start execution using pool of workers, mapping the executor callable object to the commands
            # leaving the `with` block terminates the pool, also when a simulator fails
            with Pool(processes=self.jobs) as pool:
                pool.map(executor, commands_and_working_dirs)
        except KeyboardInterrupt:
            logging.info('Pool is terminated')
            self.workspace_manager.clean()
            return False

        elapsed = timeit.default_timer() - start_time
        logging.info("run elapsed time {:.3f} seconds".format(elapsed))

        return True

    def get_data(self):
        """
        Takes all output files from the working directories of the last run (like run_1, run_2),
        merges their content to form pymchelper Estimator objects.
        For each of the output file a single Estimator objects is created, which holds numpy arrays with results.
        Return dictionary with keys being output filenames, and values being Estimator objects
        """
        start_time = timeit.default_timer()

        # only the directories of the last run: run_* directories left by earlier runs must not be merged
        working_dirs = self.workspace_manager.working_directories_abs_paths

        estimators_dict = {}
        estimators_list = []

        if self.settings.simulator_type == SimulatorType.shieldhit:
            output_files = []
            for working_dir in working_dirs:
                output_files += sorted(glob(os.path.join(working_dir, "*.bdo")))
            logging.debug("Files to merge %s", output_files)
            estimators_list = frompattern(output_files)

        elif self.settings.simulator_type == SimulatorType.topas:
            estimators_list = get_topas_estimators(working_dirs[0])

        elif self.settings.simulator_type == SimulatorType.fluka:
            output_files = []
            for working_dir in working_dirs:
                output_files += sorted(glob(os.path.join(working_dir, "*_fort.*")))
            logging.debug("Files to merge %s", output_files)
            estimators_list = frompattern(output_files)

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
    def _set_topas_number_of_threads(input_file: Path, number_of_threads: int):
        """Sets i:Ts/NumberOfThreads in the TOPAS parameter file, adding the line if it is missing"""
        config = input_file.read_text()
        if "i:Ts/NumberOfThreads" in config:
            pattern = r"i:Ts/NumberOfThreads\s*=\s*\d+"
            replacement = f"i:Ts/NumberOfThreads = {number_of_threads}"
            config = re.sub(pattern, replacement, config)
        else:
            config = f"i:Ts/NumberOfThreads = {number_of_threads}\n" + config
        input_file.write_text(config)

    @staticmethod
    def _read_fluka_rng_seed(input_file: str) -> int:
        """
        RNG seed set by the user in the FLUKA input: WHAT(2) of the RANDOMIZ card.
        Returns 0 if there is no RANDOMIZ card or its WHAT(2) is empty.
        """
        with open(input_file, 'r') as f:
            lines = f.readlines()
        for line in lines:
            if not line.startswith('RANDOMIZ'):
                continue

            # fixed format: WHAT(2) is in columns 21-30
            what2 = line[20:30].strip()
            try:
                return int(float(what2))
            except ValueError:
                pass

            # free format: keyword, WHAT(1), WHAT(2), ... separated by spaces or commas
            fields = line.replace(",", " ").split()
            if len(fields) < 3:
                return 0
            try:
                return int(float(fields[2]))
            except ValueError:
                return 0
        return 0

    @staticmethod
    def __update_fluka_input_file(destination: str, rng_seed: int):
        """
        Updates the FLUKA input file with the new RNG seed (WHAT(2) of the RANDOMIZ card).
        If the file has no RANDOMIZ card, one is added before START: cards after START are read
        only after the transport has started.
        """
        with open(destination, 'r') as destination_file:
            lines = destination_file.readlines()

        card = Input.Card("RANDOMIZ")
        card.setWhat(1, 1.)
        card.setWhat(2, rng_seed)
        randomiz_line = card.toStr() + '\n'

        has_randomize_card = False
        for index, line in enumerate(lines):
            if line.startswith('RANDOMIZ'):
                lines[index] = randomiz_line
                has_randomize_card = True

        if not has_randomize_card:
            start_index = None
            for index, line in enumerate(lines):
                if line.startswith('START'):
                    start_index = index
                    break
            if start_index is None:
                lines.append(randomiz_line)
            else:
                lines.insert(start_index, randomiz_line)

        with open(destination, 'w') as destination_file:
            destination_file.writelines(lines)


class SingleSimulationExecutor:
    """
    Callable class responsible for execution of the single MC simulation process.
    """

    log_filename = "simulator.log"

    def __call__(self, command_and_working_dir: Tuple[List[str], str], **kwargs):
        """
        Run the command in the working directory. The simulator output (stdout and stderr) goes to
        simulator.log in the working directory; if the simulator fails, its last lines are in the error.
        """
        # we deliberately combine command and working directory in the single argument
        # as this would simplify using this class by multiprocessing module
        command, working_dir_abs_path = command_and_working_dir
        logging.debug('working directory {:s}, command {:s}'.format(working_dir_abs_path, shlex.join(command)))

        log_path = Path(working_dir_abs_path) / self.log_filename
        with open(log_path, 'w') as log_file:
            completed_process = subprocess.run(command,
                                               cwd=working_dir_abs_path,
                                               stdout=log_file,
                                               stderr=subprocess.STDOUT)

        if completed_process.returncode != 0:
            log_lines = log_path.read_text(errors='replace').splitlines()
            last_lines = "\n".join(log_lines[-20:])
            raise RuntimeError(f"{shlex.join(command)} exited with code {completed_process.returncode}, "
                               f"last lines of {log_path}:\n{last_lines}")


class WorkspaceManager:
    """
    A workspace consists of multiple working directories (i.e. run_1, run_2),
    each per one of the parallel simulation run.
    """

    def __init__(self, output_directory='.', keep_workspace_after_run=False):
        self.output_dir_absolute_path = os.path.abspath(output_directory)
        self.keep_workspace_after_run = keep_workspace_after_run
        self.working_directories_abs_paths = []

    def create_working_directories(self, simulation_input_path, job_numbers=()):
        """
        Create working directories and fill `self.working_directories_abs_paths`.
        A directory left by an earlier run is removed first, so no old output files stay in it.
        """
        self.working_directories_abs_paths = []
        for job_number in job_numbers:
            # set workspace to a subdirectory of the output_directory, with run_* pattern
            # i.e. /home/user/output/run_3
            working_dir_abs_path = os.path.join(self.output_dir_absolute_path, 'run_{:d}'.format(job_number))
            logging.info("Workspace {:s}".format(working_dir_abs_path))

            if os.path.exists(working_dir_abs_path):
                shutil.rmtree(working_dir_abs_path)
            os.makedirs(working_dir_abs_path)

            if os.path.isdir(simulation_input_path):
                # copy all files from the directory
                for directory_entry in os.listdir(simulation_input_path):
                    path_to_directory_entry = os.path.join(simulation_input_path, directory_entry)
                    if os.path.isfile(path_to_directory_entry):
                        shutil.copy2(path_to_directory_entry, working_dir_abs_path)
                logging.debug("Copying input files into {:s}".format(working_dir_abs_path))
            elif os.path.isfile(simulation_input_path):
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
