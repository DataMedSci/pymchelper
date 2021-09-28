import logging
import os
import sys


class MCEnvironment:
    """
    `MCEnvironment` subclasses are helpful to discover which MC engine (i.e. FLUKA or SHIELD-HIT12A) is being used
    they provide information about expected executable filename, by inspecting the path to executable filename
    (i.e. checking if it ends with `rfluka`) we can find corresponding code type
    """
    executable_filename = None


class FlukaEnvironment(MCEnvironment):
    """
    FLUKA Environment
    """
    executable_filename = 'rfluka'


class SH12AEnvironmentLinux(MCEnvironment):
    """
    SHIELD-HIT12A Environment for Linux
    """
    executable_filename = 'shieldhit'


class SH12AEnvironmentWindows(MCEnvironment):
    """
    SHIELD-HIT12A Environment for Windows
    """
    executable_filename = 'shieldhit.exe'


class SimulationSettings:
    """
    This class is responsible for keeping track of options for MC simulation:
      - location of the MC simulator executable
      - additional options provided by the user
      - location of the input files or directories
    Moreover this class performs automatic discovery of the MC input
    (i.e. whether this is SHIELD-HIT12A input or FLUKA input)
    """

    def __init__(self, input_path, simulator_exec_path=None, cmdline_opts=None):
        # input file or directory
        self.input_path = input_path

        # discover the type of MC engine based on the type of input files/directories
        # `self._mc_environment` is set to one of the `MCEnvironment` subclasses
        self._mc_environment = self._discover_mc_engine(input_path)

        # set `self.executable_path` to the value provided by user, or if it is missing
        # perform automatic discovery of the *location* of MC engine executable file by scanning PATH env. variable
        self.executable_path = simulator_exec_path
        if not self.executable_path:
            self.executable_path = self._discover_mc_exec_location(self._mc_environment.executable_filename)

        # set extra options (i.e. `--time 00:15:30 -v`) for the MC engine
        self.cmdline_opts = cmdline_opts if cmdline_opts else ''  # sanity check for None value
        # if extra options are provided, perform options validation
        # in case the options are not supported by MC engine, validation method will throw an exception
        if self.cmdline_opts:
            self._validate_cmdline_opt(self.cmdline_opts)

    def set_rng_seed(self, rng_seed):
        """
        This methods modifies command line options of the MC engine by setting (or overriding) the value of RNG seed
        TODO this method is specific to SH12A, more general should be added
        TODO add support for RNG seed provided as --seedofset, instead of -N
        """
        # transform option list from plain string to a list of values for easier manipulation
        options_list = self.cmdline_opts.split()

        # If RNG seed is missing on the option list, then the code below will set it to given value
        if '-N' not in options_list:
            self.cmdline_opts += " -N {:d}".format(rng_seed)
        # if RNG is present on the option list, then we override its value
        else:
            # in SHIELD-HIT12A RNG seed is specified by -N option
            index_of_rng_opt = options_list.index('-N')  # find index of '-N'
            options_list[index_of_rng_opt + 1] = str(rng_seed)  # override the value of current -N option
            self.cmdline_opts = ' '.join(options_list)  # reconstruct option string

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
        options_list = cmdline_opts.split()

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
    def _discover_mc_engine(input_path):
        """
        Analyse the input path and based on its type set proper MC engine
        In case of failure return None
        """

        # raise exception if invalid path is provided
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
        Dump all settings into a string
        """
        result = "{executable_path:s} {cmdline_opts:s}".format(
            executable_path=os.path.abspath(self.executable_path),
            cmdline_opts=self.cmdline_opts if self.cmdline_opts else ''
        )
        return result


class SH12ASettings(SimulationSettings):
    """
    TODO
    """
