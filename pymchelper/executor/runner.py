from glob import glob
import logging
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import timeit
from multiprocessing import Pool

from enum import IntEnum
from typing import List, Optional, Tuple
from pymchelper.executor.options import FlukaEnvironment, SimulationSettings

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
                 jobs: Optional[int] = None,
                 keep_workspace_after_run: bool = False,
                 output_directory: str = '.'):
        self.settings = settings

        # if jobs is not specified, use the same default as multiprocessing.Pool:
        # the number of CPUs this process may use (Python >= 3.13), otherwise the number of CPUs,
        # and 1 if the number of CPUs cannot be determined
        if jobs is None:
            if hasattr(os, "process_cpu_count"):
                jobs = os.process_cpu_count() or 1
            else:
                jobs = os.cpu_count() or 1
        self.jobs: int = jobs

        # workspace is a collection of working directories
        # this manager is responsible for creating and cleaning working directories
        self.workspace_manager = WorkspaceManager(output_directory=output_directory,
                                                  keep_workspace_after_run=keep_workspace_after_run)

    def run(self):
        """
        Execute parallel simulation processes, creating workspace (and working directories) in the `output_directory`
        In case of successful execution return True, otherwise return False
        If a simulator fails, RuntimeError is raised and the working directories are kept (also without
        `keep_workspace_after_run`), so the simulator.log of each job can be inspected
        """
        start_time = timeit.default_timer()

        environment = self.settings.mc_environment
        job_numbers = environment.job_numbers(self.jobs)

        # create working directories, each with its own copy of the input files
        self.workspace_manager.create_working_directories(simulation_input_path=self.settings.input_path,
                                                          job_numbers=job_numbers)

        commands_and_working_dirs = []
        for job_number, working_dir in zip(job_numbers, self.workspace_manager.working_directories_abs_paths):
            command = environment.job_command(self.settings, job_number, self.jobs, working_dir)
            commands_and_working_dirs.append((command, working_dir))

        # create executor callable object for current run
        executor = SingleSimulationExecutor()

        try:
            # start execution using pool of workers, mapping the executor callable object to the commands
            # leaving the `with` block terminates the pool, also when a simulator fails
            with Pool(processes=len(commands_and_working_dirs)) as pool:
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
        If `run` was not called on this Runner, all run_* directories in the workspace are read.
        For each of the output file a single Estimator objects is created, which holds numpy arrays with results.
        Return dictionary with keys being output filenames, and values being Estimator objects
        """
        start_time = timeit.default_timer()

        # only the directories of the last run: run_* directories left by earlier runs must not be merged
        working_dirs = self.workspace_manager.working_directories_abs_paths
        if not working_dirs:
            # run() was not called on this Runner: read the working directories found in the workspace
            working_dirs_pattern = os.path.join(self.workspace_manager.output_dir_absolute_path, "run_*")
            working_dirs = sorted(glob(working_dirs_pattern))
            if not working_dirs:
                raise FileNotFoundError(f"No working directories {working_dirs_pattern}")

        estimators_dict = {}

        if self.settings.simulator_type == SimulatorType.topas:
            estimators_list = get_topas_estimators(working_dirs[0])
        else:
            output_files = []
            for working_dir in working_dirs:
                output_files_pattern = os.path.join(working_dir, self.settings.mc_environment.output_files_pattern)
                output_files += sorted(glob(output_files_pattern))
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

    # yaptide calls Runner._Runner__update_fluka_input_file
    __update_fluka_input_file = staticmethod(FlukaEnvironment.update_input_file)  # skipcq: PTC-W0037


class SingleSimulationExecutor:
    """
    Callable class responsible for execution of the single MC simulation process.
    """

    log_filename = "simulator.log"
    # number of the last lines of the simulator output shown in the error when the simulator fails
    log_lines_in_error = 20

    def __call__(self, command_and_working_dir: Tuple[List[str], str], **kwargs):
        """
        Run the command in the working directory. The simulator output (stdout and stderr) goes to
        simulator.log in the working directory; if the simulator fails, its last lines are in the error.
        """
        # we deliberately combine command and working directory in the single argument
        # as this would simplify using this class by multiprocessing module
        command, working_dir_abs_path = command_and_working_dir
        logging.debug('working directory %s, command %s', working_dir_abs_path, shlex.join(command))

        log_path = Path(working_dir_abs_path) / self.log_filename
        with open(log_path, 'w') as log_file:
            # check=False: the return code is checked below, so the error can show the simulator output
            completed_process = subprocess.run(command,
                                               cwd=working_dir_abs_path,
                                               stdout=log_file,
                                               stderr=subprocess.STDOUT,
                                               check=False)

        if completed_process.returncode != 0:
            log_lines = log_path.read_text(errors='replace').splitlines()
            last_lines = "\n".join(log_lines[-self.log_lines_in_error:])
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
        Raises ValueError, before anything is removed, if the input is inside one of these directories.
        """
        input_real_path = Path(simulation_input_path).resolve()
        for job_number in job_numbers:
            working_dir_real_path = Path(self.output_dir_absolute_path, f'run_{job_number:d}').resolve()
            if input_real_path.is_relative_to(working_dir_real_path):
                raise ValueError(f"Input {simulation_input_path} is inside the working directory "
                                 f"{working_dir_real_path}, which is removed before the run; "
                                 "move the input or choose another workspace directory")

        self.working_directories_abs_paths = []
        for job_number in job_numbers:
            # set workspace to a subdirectory of the output_directory, with run_* pattern
            # i.e. /home/user/output/run_3
            working_dir_abs_path = os.path.join(self.output_dir_absolute_path, f'run_{job_number:d}')
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
