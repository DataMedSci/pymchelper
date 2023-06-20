import logging
import os
import sys
from typing import Optional, Type
from pymchelper.executor.environment import (
    FlukaEnvironment, MCEnvironment, SH12AEnvironmentLinux, SH12AEnvironmentWindows, TopasEnvironment)
from pymchelper.executor.options import SimulationOptions
from pymchelper.executor.types import PathLike

from pymchelper.simulator_type import SimulatorType


class SimulationSettings:
    """Class responsible for keeping track of options for MC simulation.

    Options:
      - location of the MC simulator executable
      - additional options provided by the user
      - location of the input files or directories
    Moreover this class performs automatic discovery of the MC input
    (i.e. whether this is SHIELD-HIT12A input or FLUKA input)
    """

    def __init__(self, input_path: PathLike, simulator_exec_path: Optional[PathLike] = None,
                 cmdline_opts: Optional[str] = None, simulator_type: Optional[SimulatorType] = None):
        """Initialize the object."""
        # input file or directory
        self.options = SimulationOptions(input_path=input_path,
                                         simulator_type=simulator_type,
                                         simulator_exec_path=simulator_exec_path,
                                         cmdline_opts=cmdline_opts if cmdline_opts else '')
        self.__setup()

    def __setup(self):
        """Perform automatic discovery of the MC input and executable file."""
        # discover the type of MC engine based on the type of input files/directories
        # `self._mc_environment` is set to one of the `MCEnvironment` subclasses
        self.__setup_environment()

        self.__discover_mc_exec_location()

        # if extra options are provided, perform options validation
        # in case the options are not supported by MC engine, validation method will throw an exception
        self.__validate_cmdline_opt()

    def __setup_environment(self):
        environment: Optional[Type[MCEnvironment]] = None
        if not self.options.simulator_type:
            environment = self.__discover_mc_engine()
        else:
            if self.options.simulator_type == SimulatorType.shieldhit:
                if sys.platform == 'win32':
                    environment = SH12AEnvironmentWindows
                else:
                    environment = SH12AEnvironmentLinux
            elif self.options.simulator_type == SimulatorType.fluka:
                environment = FlukaEnvironment
            elif self.options.simulator_type == SimulatorType.topas:
                environment = TopasEnvironment
        if not environment:
            raise Exception("Unable to determine MC engine type")
        self.__mc_environment = environment(options=self.options)

    def __validate_cmdline_opt(self):
        if self.__mc_environment:
            self.__mc_environment.validate_cmdline_opt()

    def __discover_mc_engine(self) -> Optional[Type[MCEnvironment]]:
        """Analyse the input path and based on its type set proper MC engine.

        In case of failure return None
        """
        # raise exception if invalid path is provided
        input_path = self.options.input_path
        if not os.path.exists(input_path):
            raise Exception("Input path {:s} doesn't exists".format(input_path))

        # Fluka input files are provided as the single file
        # TODO cross-check if the `*.inp` extension is needed  # skipcq: PYL-W0511
        if os.path.isfile(input_path):
            return FlukaEnvironment
        # SHIELD-HIT12A input is in the form of directory with multiple files
        # TODO add a check if the directory contains (beam.dat, mat.dat, geo.dat and detect.dat)  # skipcq: PYL-W0511
        if os.path.isdir(input_path):
            # in case pymchelper runs on Windows choose a SHIELD-HIT12A environment which is Windows specific
            # (executable file being `shieldhit.exe` instead of `shieldhit`)
            if sys.platform == 'win32':
                return SH12AEnvironmentWindows
            return SH12AEnvironmentLinux
        return None

    def __discover_mc_exec_location(self):
        """
        Scans PATH variable for the possible location of the MC engine exec_filename.
        Works on POSIX (Linux and MacOSX) and Windows systems
        """
        exec_filename = self.__mc_environment.executable_file_name()
        if self.options.simulator_exec_path:
            return
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

    def set_rng_seed(self, rng_seed: int):
        """Set random number generator seed."""
        self.__mc_environment.set_rng_seed(rng_seed)

    def set_no_of_primaries(self, number_of_primaries: int):
        """Set number of primaries for the simulation."""
        self.__mc_environment.set_no_of_primaries(number_of_primaries)

    def __str__(self):
        """
        Dump all settings into a string
        """
        options = self.options
        path = os.path.abspath(str(options.simulator_exec_path)) if options.simulator_exec_path else ''
        result = "{executable_path:s} {cmdline_opts:s}".format(executable_path=path, cmdline_opts=options.cmdline_opts)
        return result
