import os, sys

import logging

logger = logging.getLogger(__name__)

class MCOptions:
    def __init__(self, executable_path=None, user_opt=None):
        if executable_path is not None:
            self.executable_path = executable_path
        else:
            self.executable_path = self._discover_mc_executable()

    def _discover_mc_executable(self):
        pass
        # dirs_with_mc_exe = []
        # for item in sys.path:
        #     logger.debug("Inspecting {:s}".format(item))
        #     if os.path.exists(item) and self._mc_enviroment.executable_file in os.listdir(item):
        #         dirs_with_mc_exe.append(item)
        #
        # if not dirs_with_mc_exe:
        #     raise Exception("Executable {:s} not found in PATH ({:s})".format(self._mc_enviroment.executable_file,
        #                                                                       ",".join(sys.path)))
        #
        # return os.path.join(dirs_with_mc_exe[0], self._mc_enviroment.executable_file)



class SH12AOptions(MCOptions):
    pass