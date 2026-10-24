from copy import deepcopy
import logging
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import List, Optional, Type

from pymchelper.flair import Input
from pymchelper.simulator_type import SimulatorType


def split_options(options: str) -> List[str]:
    """
    Split command line options like the shell of this platform does, so a quoted value with spaces stays one item.
    On Windows backslashes are path separators, not escape characters, so they are kept.
    """
    if os.name != 'nt':
        return shlex.split(options)
    items = shlex.split(options, posix=False)
    # in non-POSIX mode the quotes stay in the item, remove the ones around it
    return [item[1:-1] if len(item) > 1 and item[0] == item[-1] and item[0] in '"\'' else item for item in items]


def join_options(options: List[str]) -> str:
    """Join command line options into one string, which `split_options` splits back into the same items"""
    if os.name != 'nt':
        return shlex.join(options)
    return subprocess.list2cmdline(options)


def job_rng_seed(user_rng_seed: int, job_number: int, jobs: int) -> int:
    """
    RNG seed of one of the parallel jobs: the seed given by the user times the number of jobs, plus the job number.
    Jobs of one run get different seeds, and runs with different user seeds and the same number of jobs
    share no seed, so their results can be merged.
    Runs with different numbers of jobs may share seeds (user seed 2 with 2 jobs gives 5 and 6,
    user seed 1 with 4 jobs gives 5 to 8), so runs to be merged must use the same number of jobs.
    """
    return user_rng_seed * jobs + job_number


class MCEnvironment:
    """
    `MCEnvironment` subclasses are helpful to discover which MC engine (i.e. FLUKA or SHIELD-HIT12A) is being used
    they provide information about expected executable filename, by inspecting the path to executable filename
    (i.e. checking if it ends with `rfluka`) we can find corresponding code type.
    They also prepare the working directory of each parallel job and the command to run in it.
    """
    executable_filename: Optional[str] = None
    simulator_type: Optional[SimulatorType] = None
    # files with results in the working directory, merged after the run
    output_files_pattern: Optional[str] = None

    @staticmethod
    def job_numbers(jobs: int) -> List[int]:
        """Numbers of the parallel jobs (each runs in its own working directory run_N): 1 to `jobs`"""
        return list(range(1, jobs + 1))

    @staticmethod
    def job_command(settings: "SimulationSettings", job_number: int, jobs: int, working_dir: str) -> List[str]:
        """
        Prepare the input files in the working directory of the job (they are already copied there)
        and return the command which runs the job in that directory
        """
        raise NotImplementedError


class FlukaEnvironment(MCEnvironment):
    """
    FLUKA Environment
    """
    executable_filename = 'rfluka'
    simulator_type = SimulatorType.fluka
    output_files_pattern = "*_fort.*"
    # FLUKA accepts RANDOMIZ WHAT(2) below 9E8
    rng_seed_limit = 900000000

    @staticmethod
    def job_command(settings: "SimulationSettings", job_number: int, jobs: int, working_dir: str) -> List[str]:
        """
        Write the RNG seed of the job into the copy of the input file (RANDOMIZ card),
        the command is rfluka with its options, followed by that copy
        """
        input_file_copy = str(Path(working_dir) / Path(settings.input_path).name)
        user_rng_seed = FlukaEnvironment.read_rng_seed(settings.input_path)
        rng_seed = job_rng_seed(user_rng_seed, job_number, jobs)
        if rng_seed >= FlukaEnvironment.rng_seed_limit:
            raise ValueError(f"FLUKA RNG seed of job {job_number} would be {rng_seed} "
                             f"(RANDOMIZ WHAT(2) {user_rng_seed} * {jobs} jobs + {job_number}), "
                             f"FLUKA needs it below {FlukaEnvironment.rng_seed_limit}; use a smaller WHAT(2)")
        FlukaEnvironment.update_input_file(input_file_copy, rng_seed)
        command = settings.command_as_list()
        command.append(input_file_copy)
        return command

    @staticmethod
    def read_rng_seed(input_file: str) -> int:
        """
        RNG seed set by the user in the FLUKA input: WHAT(2) of the first RANDOMIZ card.
        Returns 0 if there is no RANDOMIZ card or its WHAT(2) is empty.
        """
        fluka_input = Input.Input()
        fluka_input.read(str(input_file))
        randomiz_cards = fluka_input.cardsSorted("RANDOMIZ")
        if not randomiz_cards:
            return 0
        return randomiz_cards[0].intWhat(2)

    @staticmethod
    def update_input_file(destination: str, rng_seed: int):
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


class SH12AEnvironment(MCEnvironment):
    """SHIELD-HIT12A Environment, common part for Linux and Windows"""

    simulator_type = SimulatorType.shieldhit
    output_files_pattern = "*.bdo"

    @staticmethod
    def job_command(settings: "SimulationSettings", job_number: int, jobs: int, working_dir: str) -> List[str]:
        """
        The command is shieldhit with its options and the RNG seed offset of the job (-N),
        followed by the working directory, from which shieldhit reads the input files
        """
        user_rng_seed = settings.rng_seed
        if user_rng_seed is None:
            user_rng_seed = 0
        job_settings = deepcopy(settings)  # do not modify original settings
        job_settings.set_rng_seed(job_rng_seed(user_rng_seed, job_number, jobs))
        command = job_settings.command_as_list()
        command.append(working_dir)
        return command


class SH12AEnvironmentLinux(SH12AEnvironment):
    """
    SHIELD-HIT12A Environment for Linux
    """
    executable_filename = 'shieldhit'


class SH12AEnvironmentWindows(SH12AEnvironment):
    """
    SHIELD-HIT12A Environment for Windows
    """
    executable_filename = 'shieldhit.exe'


class TopasEnvironment(MCEnvironment):
    """TOPAS Environment"""

    executable_filename = 'topas'
    simulator_type = SimulatorType.topas

    @staticmethod
    def job_numbers(jobs: int) -> List[int]:
        """
        TOPAS runs as one job in one working directory: it parallelizes itself,
        with the number of threads in the parameter file set to the number of jobs
        """
        return [1]

    @staticmethod
    def job_command(settings: "SimulationSettings", job_number: int, jobs: int, working_dir: str) -> List[str]:
        """
        Set the number of threads in the copy of the parameter file to the number of jobs,
        the command is topas followed by that file. TOPAS reads the RNG seed from i:Ts/Seed in that file.
        """
        input_file_copy = Path(working_dir) / Path(settings.input_path).name
        TopasEnvironment.set_number_of_threads(input_file_copy, jobs)
        return [os.path.abspath(settings.executable_path), input_file_copy.name]

    @staticmethod
    def set_number_of_threads(input_file: Path, number_of_threads: int):
        """Sets i:Ts/NumberOfThreads in the TOPAS parameter file, adding the line if it is missing"""
        config = input_file.read_text()
        if "i:Ts/NumberOfThreads" in config:
            pattern = r"i:Ts/NumberOfThreads\s*=\s*\d+"
            replacement = f"i:Ts/NumberOfThreads = {number_of_threads}"
            config = re.sub(pattern, replacement, config)
        else:
            config = f"i:Ts/NumberOfThreads = {number_of_threads}\n" + config
        input_file.write_text(config)


class SimulationSettings:
    """
    This class is responsible for keeping track of options for MC simulation:

      - location of the MC simulator executable
      - additional options provided by the user
      - location of the input files or directories

    Moreover this class performs automatic discovery of the MC input
    (i.e. whether this is SHIELD-HIT12A, Fluka or TOPAS input)
    """

    def __init__(self, input_path: str, simulator_type: Optional[SimulatorType] = None,
                 simulator_exec_path: Optional[str] = None, cmdline_opts: Optional[str] = None):
        # Input file or directory
        self.input_path = input_path

        self.mc_environment: Optional[Type[MCEnvironment]] = None

        # Set `self.mc_environment` to the proper `MCEnvironment` subclass
        # If `simulator_type` is provided by user, then we use it to set proper `MCEnvironment` subclass
        # Otherwise, we try to guess based on provided input path
        if simulator_type:
            if simulator_type == SimulatorType.shieldhit:
                if sys.platform == 'win32':
                    self.mc_environment = SH12AEnvironmentWindows
                else:
                    self.mc_environment = SH12AEnvironmentLinux
            elif simulator_type == SimulatorType.fluka:
                self.mc_environment = FlukaEnvironment
            elif simulator_type == SimulatorType.topas:
                self.mc_environment = TopasEnvironment
        else:
            self.mc_environment = self._discover_mc_engine(input_path)

        if not self.mc_environment:
            raise Exception(f"Unable to determine MC engine type for {input_path}")

        self.simulator_type = self.mc_environment.simulator_type

        # set `self.executable_path` to the value provided by user, or if it is missing
        # perform automatic discovery of the *location* of MC engine executable file by scanning PATH env. variable
        self.executable_path: str = simulator_exec_path or \
            self._discover_mc_exec_location(self.mc_environment.executable_filename)

        # set extra options (i.e. `--time 00:15:30 -v`) for the MC engine
        self.cmdline_opts = cmdline_opts if cmdline_opts else ''  # sanity check for None value
        # if extra options are provided, perform options validation
        # in case the options are not supported by MC engine, validation method will throw an exception
        if self.cmdline_opts:
            self._validate_cmdline_opt(self.cmdline_opts)

        # RNG seed offset of SHIELD-HIT12A (-N), None if not given; kept out of `cmdline_opts`
        self.rng_seed: Optional[int] = None
        if self.simulator_type == SimulatorType.shieldhit:
            self._move_rng_seed_out_of_cmdline_opts()

    def _move_rng_seed_out_of_cmdline_opts(self):
        """
        Moves the SHIELD-HIT12A RNG seed offset, given as -N or as its long form --seedoffset
        (also as --seedoffset=VALUE), from `cmdline_opts` to `rng_seed`.
        If it is given more than once, the last value is used.
        Raises ValueError if the value is missing or is not an integer.
        """
        options_list = split_options(self.cmdline_opts)
        other_options = []
        index = 0
        while index < len(options_list):
            option = options_list[index]
            if option in ('-N', '--seedoffset'):
                if index + 1 >= len(options_list):
                    raise ValueError(f"{option} needs an integer RNG seed offset")
                value = options_list[index + 1]
                index += 2
            elif option.startswith('--seedoffset='):
                option, value = option.split('=', 1)
                index += 1
            else:
                other_options.append(option)
                index += 1
                continue
            try:
                self.rng_seed = int(value)
            except ValueError:
                raise ValueError(f"{option} needs an integer RNG seed offset, got {value!r}") from None
        self.cmdline_opts = join_options(other_options)

    def set_rng_seed(self, rng_seed: int):
        """
        Sets the RNG seed, passed to the MC engine as -N (SHIELD-HIT12A RNG seed offset).
        TODO this method is specific to SH12A, more general should be added
        """
        self.rng_seed = int(rng_seed)

    def command_as_list(self) -> list:
        """
        MC engine executable followed by its command line options and the RNG seed (-N, if set),
        as a list for the subprocess module.
        The executable path is one item even if it contains spaces, options are split like a shell does,
        so a quoted value with spaces stays one item.
        """
        command = [os.path.abspath(self.executable_path)]
        command += split_options(self.cmdline_opts)
        if self.rng_seed is not None:
            command += ['-N', str(self.rng_seed)]
        return command

    def set_no_of_primaries(self, number_of_primaries):
        """
        This methods modifies command line options of the MC engine by setting (or overriding) the number of primaries
        to be simulated by each of the parallel jobs
        TODO this method is specific to SH12A, more general should be added
        TODO add support for no of primaries provided as --nstat, instead of -n
        """
        # transform option list from plain string to a list of values for easier manipulation
        options_list = self.cmdline_opts.split()

        # If no of primaries is missing on the option list, then the code below will set it to given value
        if '-n' not in options_list:
            self.cmdline_opts += " -n {:d}".format(number_of_primaries)
        else:
            # see `set_rng_seed` for the logic
            index_of_prim_opt = options_list.index('-n')
            options_list[index_of_prim_opt + 1] = str(number_of_primaries)
            self.cmdline_opts = ' '.join(options_list)

    @staticmethod
    def _validate_cmdline_opt(cmdline_opts):
        """
        TODO this method is specific to SH12A, more general should be added
        """
        # transform option list from plain string to a list of values for easier manipulation
        options_list = split_options(cmdline_opts)

        # transform option list to a set to ease finding common part of unsupported and current options
        options_set = set(options_list)
        # set of options which cannot be overwritten by the user
        # these include locations of the input files which are fixed to the temporary workspace directories
        # generated by the `pymchelper` code
        unsupported = {'-b', '--beamfile', '-g', '--geofile', '-m', '--matfile', '-d', '--detectfile'}
        # raise an error if some of the unsupported option was provided by user (i.e. via -m option to `runmc` command)
        if options_set & unsupported:
            # TODO replace exception with warning and ignore such options  # skipcq: PYL-W0511
            raise SyntaxError("Unsupported option encountered: {:s}".format(",".join(options_set & unsupported)))

    @staticmethod
    def _discover_mc_engine(input_path_str: str):
        """
        Analyse the input path and based on its type set proper MC engine
        In case of failure return None
        """
        input_path = Path(input_path_str)
        # raise exception if invalid path is provided
        if not input_path.exists():
            raise Exception("Input path {:s} doesn't exists".format(input_path))

        # Fluka and TOPAS input files are provided as the single file
        # We return proper MC engine based on the file extension
        if input_path.is_file():
            if input_path_str.endswith('.inp'):
                return FlukaEnvironment
            if input_path_str.endswith('.txt'):
                return TopasEnvironment
        # SHIELD-HIT12A input is in the form of directory with multiple files
        elif input_path.is_dir():
            # We check if directory contains the required SHIELDHIT-12A input files
            if all(input_path.joinpath(file).exists() for file in ['beam.dat', 'mat.dat', 'geo.dat', 'detect.dat']):
                # in case pymchelper runs on Windows choose a SHIELDHIT-12A environment which is Windows specific
                # (executable file being `shieldhit.exe` instead of `shieldhit`)
                if sys.platform == 'win32':
                    return SH12AEnvironmentWindows
                return SH12AEnvironmentLinux
        return None

    @staticmethod
    def _discover_mc_exec_location(exec_filename):
        """
        Scans PATH variable for the possible location of the MC engine exec_filename.
        Works on POSIX (Linux and MacOSX) and Windows systems
        """

        # PATH variable contains list of directories being separated by : on POSIX systems
        # and by ; on Windows systems. Here we set proper separator
        separator_char = ':'
        if sys.platform == 'win32':
            separator_char = ';'

        list_of_directories = []
        # loop over all directories in PATH env variable
        for path_directory_entry in os.environ['PATH'].split(separator_char):

            logging.debug("Inspecting {:s}".format(path_directory_entry))

            # check if PATH entry is a proper directory
            # some malicious users can add a files to PATH as well (although it doesn't make any sense)
            if os.path.isdir(path_directory_entry):

                # scan a PATH entry and loop over all filenames inside PATH entry directory using `os.listdir`
                if exec_filename in os.listdir(path_directory_entry):

                    # add a directories for which we encounter `exec_filename`
                    # (MC engine filename, like `rfluka` or `shieldhit`)
                    list_of_directories.append(path_directory_entry)

        # raise exception if MC engine not found
        if not list_of_directories:
            raise Exception("Executable {:s} not found in PATH ({:s})".format(exec_filename, ",".join(sys.path)))

        # if `exec_filename` is found in multiple location, return full path to the first location (directory+filename)
        return os.path.join(list_of_directories[0], exec_filename)

    def __str__(self):
        """
        The command of `command_as_list`, items separated by spaces
        """
        return " ".join(self.command_as_list())


class SH12ASettings(SimulationSettings):
    """
    TODO
    """
