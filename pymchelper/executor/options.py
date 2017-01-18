import os, sys

import logging

logger = logging.getLogger(__name__)


class FlukaEnviroment:
    executable_file = 'rfluka'


class SH12AEnviroment:
    executable_file = 'shieldhit'


class MCOptions:
    def __init__(self, input_cfg, executable_path=None, user_opt=None):
        self._mc_enviroment = self._discover_mc_enging(input_cfg)
        self.executable_path = executable_path
        if self.executable_path is None:
            self.executable_path = self._discover_mc_executable()
        self.user_opt = user_opt
        self._validate_user_opt(self.user_opt)
        self.workspace = '.'


    @staticmethod
    def _validate_user_opt(user_opt):
        options_list = user_opt.split()
        options_set = set(options_list)
        unsupported = set(('-b', '--beamfile', '-g', '--geofile', '-m', '--matfile', '-d', '--detectfile'))
        if options_set & unsupported:
            raise SyntaxError("Unsupported option encounted: {:s}".format(",".join(options_set & unsupported)))
        if len(options_list) > 1:
            last_item = options_list[-1]
            before_last_item = options_list[-2]
            single_options = set(('-h', '--help', '-V', '--version', '-v', '--verbose', '-s', '--silent',
                                  '-l', '--legacy-bdo'))
            if not last_item.startswith('-'):
                if before_last_item in single_options:
                    raise SyntaxError("Seems like workspace: {:s}".format(last_item))
                elif len(options_list) > 2 and options_list[-3].startswith('-'):
                    raise SyntaxError("Seems like workspace: {:s}".format(last_item))
        if len(options_list) == 1 and not options_list[0].startswith('-'):
            raise SyntaxError("Seems like workspace: {:s}".format(options_list[0]))

    def _discover_mc_enging(self, input_cfg):
        if not os.path.exists(input_cfg):
            raise Exception("Input path {:s} doesn't exists".format(input_cfg))
        if os.path.isfile(input_cfg):
            return FlukaEnviroment
        if os.path.isdir(input_cfg):
            return SH12AEnviroment

    def _discover_mc_executable(self):
        dirs_with_mc_exe = []
        for item in sys.path:
            logger.debug("Inspecting {:s}".format(item))
            if os.path.exists(item) and self._mc_enviroment.executable_file in os.listdir(item):
                dirs_with_mc_exe.append(item)

        if not dirs_with_mc_exe:
            raise Exception("Executable {:s} not found in PATH ({:s})".format(self._mc_enviroment.executable_file,
                                                                              ",".join(sys.path)))

        return os.path.join(dirs_with_mc_exe[0], self._mc_enviroment.executable_file)

    def __str__(self):
        result = "{exec:s} {options:s} {workspace:s}".format(
            exec=self.executable_path,
            options=self.user_opt,
            workspace=self.workspace
        )
        return result


class SH12AOptions(MCOptions):
    pass
