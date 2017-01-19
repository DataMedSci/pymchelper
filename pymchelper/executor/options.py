import os
import sys
import logging

logger = logging.getLogger(__name__)


class FlukaEnviroment:
    executable_file = 'rfluka'


class SH12AEnviroment:
    executable_file = 'shieldhit'


class MCOptions:
    def __init__(self, input_cfg, executable_path=None, user_opt=None):
        self.input_cfg = input_cfg
        self._mc_enviroment = self._discover_mc_engine()
        self.executable_path = executable_path
        if self.executable_path is None:
            self.executable_path = self._discover_mc_executable()
        self.user_opt = user_opt
        self._validate_user_opt(self.user_opt)
        self.workspace = '.'

    def set_rng_seed(self, rng_seed):
        options_list = self.user_opt.split()
        if '-N' not in options_list:
            self.user_opt += " -N {:d}".format(rng_seed)
        else:
            location = options_list.index('-N')
            options_list[location+1] = str(rng_seed)
            self.user_opt = ' '.join(options_list)

    def set_nstat(self, nstat):
        options_list = self.user_opt.split()
        if '-n' not in options_list:
            self.user_opt += " -n {:d}".format(nstat)
        else:
            location = options_list.index('-n')
            options_list[location+1] = str(nstat)
            self.user_opt = ' '.join(options_list)

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

    def _discover_mc_engine(self):
        if not os.path.exists(self.input_cfg):
            raise Exception("Input path {:s} doesn't exists".format(self.input_cfg))
        if os.path.isfile(self.input_cfg):
            return FlukaEnviroment
        if os.path.isdir(self.input_cfg):
            return SH12AEnviroment

    def _discover_mc_executable(self):
        dirs_with_mc_exe = []
        for item in sys.path:
            logger.debug("Inspecting {:s}".format(item))
            if os.path.exists(item) and os.path.isdir(item) and self._mc_enviroment.executable_file in os.listdir(item):
                dirs_with_mc_exe.append(item)

        if not dirs_with_mc_exe:
            raise Exception("Executable {:s} not found in PATH ({:s})".format(self._mc_enviroment.executable_file,
                                                                              ",".join(sys.path)))

        return os.path.join(dirs_with_mc_exe[0], self._mc_enviroment.executable_file)

    def __str__(self):
        result = "{executable:s} {options:s} {workspace:s}".format(
            executable=os.path.abspath(self.executable_path),
            options=self.user_opt,
            workspace=os.path.abspath(self.workspace)
        )
        return result


class SH12AOptions(MCOptions):
    pass
