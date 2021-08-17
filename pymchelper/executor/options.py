import logging
import os
import sys


class FlukaEnvironment:
    """
    TODO
    """
    executable_file = 'rfluka'


class SH12AEnvironmentLinux:
    """
    TODO
    """
    executable_file = 'shieldhit'


class SH12AEnvironmentWindows:
    """
    TODO
    """
    executable_file = 'shieldhit.exe'


class MCOptions:
    """
    TODO
    """
    def __init__(self, input_path, executable_path=None, user_opt=None):
        self.input_path = input_path
        self._mc_environment = self._discover_mc_engine()
        self.executable_path = executable_path
        if self.executable_path is None:
            self.executable_path = self._discover_mc_executable()
        self.user_opt = user_opt if user_opt else ''
        if self.user_opt:
            self._validate_user_opt(self.user_opt)
        self.workspace = '.'

    def set_rng_seed(self, rng_seed):
        """
        TODO
        """
        options_list = self.user_opt.split()
        if '-N' not in options_list:
            self.user_opt += " -N {:d}".format(rng_seed)
        else:
            location = options_list.index('-N')
            options_list[location + 1] = str(rng_seed)
            self.user_opt = ' '.join(options_list)

    def set_no_of_primaries(self, number_of_primaries):
        """
        TODO
        """
        options_list = self.user_opt.split()
        if '-n' not in options_list:
            self.user_opt += " -n {:d}".format(number_of_primaries)
        else:
            location = options_list.index('-n')
            options_list[location + 1] = str(number_of_primaries)
            self.user_opt = ' '.join(options_list)

    @staticmethod
    def _validate_user_opt(user_opt):
        """
        TODO
        """
        options_list = user_opt.split()
        options_set = set(options_list)
        unsupported = {'-b', '--beamfile', '-g', '--geofile', '-m', '--matfile', '-d', '--detectfile'}
        if options_set & unsupported:
            raise SyntaxError("Unsupported option encountered: {:s}".format(",".join(options_set & unsupported)))
        if len(options_list) > 1:
            last_item = options_list[-1]
            before_last_item = options_list[-2]
            single_options = {'-h', '--help', '-V', '--version', '-v', '--verbose', '-s', '--silent',
                              '-l', '--legacy-bdo'}
            if not last_item.startswith('-'):
                if before_last_item in single_options:
                    raise SyntaxError("Seems like workspace: {:s}".format(last_item))
                if len(options_list) > 2 and options_list[-3].startswith('-'):
                    raise SyntaxError("Seems like workspace: {:s}".format(last_item))
        if len(options_list) == 1 and not options_list[0].startswith('-'):
            raise SyntaxError("Seems like workspace: {:s}".format(options_list[0]))

    def _discover_mc_engine(self):
        """
        TODO
        """
        if not os.path.exists(self.input_path):
            raise Exception("Input path {:s} doesn't exists".format(self.input_path))
            return None
        if os.path.isfile(self.input_path):
            return FlukaEnvironment
        if os.path.isdir(self.input_path):
            if sys.platform == 'win32':
                return SH12AEnvironmentWindows
            return SH12AEnvironmentLinux

    def _discover_mc_executable(self):
        """
        TODO
        """
        dirs_with_mc_exe = []
        split_char = ':'
        if sys.platform == 'win32':
            split_char = ';'
        for item in os.environ['PATH'].split(split_char):
            logging.debug("Inspecting {:s}".format(item))
            if os.path.isdir(item) and self._mc_environment.executable_file in os.listdir(item):
                dirs_with_mc_exe.append(item)

        if not dirs_with_mc_exe:
            raise Exception("Executable {:s} not found in PATH ({:s})".format(self._mc_environment.executable_file,
                                                                              ",".join(sys.path)))

        return os.path.join(dirs_with_mc_exe[0], self._mc_environment.executable_file)

    def __str__(self):
        result = "{executable:s} {options:s} {workspace:s}".format(
            executable=os.path.abspath(self.executable_path),
            options=self.user_opt if self.user_opt else '',
            workspace=os.path.abspath(self.workspace)
        )
        return result


class SH12AOptions(MCOptions):
    """
    TODO
    """
    pass
