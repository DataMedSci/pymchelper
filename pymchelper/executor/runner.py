"""
Module allows to run MC binary program, kill it, check current status, obtain current output (from stdout),
"""

import os
import threading
import re
import sys
import logging
from enum import IntEnum
from subprocess import Popen, PIPE

from pymchelper.executor.exceptions import ExecutorError, ProcessAlreadyStarted

logger = logging.getLogger(__name__)


class MCOutType(IntEnum):
    raw = 0
    plot = 1
    txt = 2


class FlukaEnviroment:
    executable_file = 'rfluka'


class SH12AEnviroment:
    executable_file = 'shieldhit'


class Executable:
    """
    Class which is main wrapper to manage MC binary program (rfluka, shieldhit).
    """
    RUNNING_STATUS = 'running'
    FINISHED_STATUS = 'finished'
    FAILED_STATUS = 'failed'
    TERMINATED_STATUS = 'terminated'

    def __init__(self, input_cfg, executable_path=None, mc_args=None):
        """
        :param input_cfg: File or folder with input files.
        Fluka is using single input file, while SHIELD-HIT12A uses folders
        :param executable_path: Path to binary file (rfluka, shieldhit). If not set, we'll try to discover it.
        """
        self._mc_enviroment = self._discover_mc_enging(input_cfg)
        self._input_cfg = input_cfg
        if executable_path is not None:
            self.executable_path = executable_path
        else:
            self.executable_path = self._discover_mc_executable()
        self._mc_args = mc_args
        self._process = None
        self.status = None
        self.output = ""
        self.last_stdout_line = None
        self.stderr = None
        self.special_lines = []
        self.communicate = None

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

    def run(self):
        """
        Method starting shieldhit process and supervisor thread
        Raise:
            ProcessAlreadyStarted - if it's tried to run process while it's already running
        """
        if self.status == Executable.RUNNING_STATUS:
            raise ProcessAlreadyStarted

        self._clear_attributes()

        try:
            if self._mc_args:
                print("args", self._mc_args)
                t = [self.executable_path, self._input_cfg] + self._mc_args.split()
                print("t", t)
                self._process = Popen(t, stdout=PIPE, stderr=PIPE,
                                      universal_newlines=True)
            else:
                self._process = Popen([self.executable_path, self._input_cfg], stdout=PIPE, stderr=PIPE,
                                      universal_newlines=True)
        except (PermissionError, FileNotFoundError):
            raise ExecutorError("Problem with executing: " + self.executable_path)

        self.status = Executable.RUNNING_STATUS

        self._supervisor = Monitor(self._process, self)
        self._supervisor_thread = threading.Thread(target=self._supervisor.check_status, args=())
        self._supervisor_thread.start()

    def kill(self):
        if not self._process:
            raise ExecutorError('Firstly you have to run process')

        self._process.terminate()
        # is needed to finally kill defunct process
        os.waitpid(self._process.pid, 0)

        self.status = Executable.TERMINATED_STATUS
        self._process = None

    def _read_end_status(self):
        if self.status != Executable.TERMINATED_STATUS:
            s = self._process.returncode
            if s == 0:
                self.status = Executable.FINISHED_STATUS
            else:
                self.status = Executable.FAILED_STATUS

    def _clear_attributes(self):
        """
        Clear attributes
        Necessary in case run() is used twice
        """
        self._process = None
        self.status = None
        self.output = ""
        self.last_stdout_line = None
        self.stderr = None
        self.special_lines = []
        self.communicate = None

    @property
    def pid(self):
        if self._process:
            return self._process.pid
        else:
            return None


class TempExecutor:
    def __init__(self, input_cfg, executable_path=None, mc_args=None):
        self._input_cfg = input_cfg
        self._executable_path = executable_path
        self._mc_args = mc_args

    def run(self):
        import tempfile
        import shutil
        # make temp dir
        working_dir = tempfile.mkdtemp()  # make temp working dir for converter output files
        logger.info("Creating directory {:s}".format(working_dir))

        # copy input to temp dir
        shutil.copytree(self._input_cfg, os.path.join(working_dir, "work"))

        # run in temp dir
        s = Executable(executable_path=self._executable_path,
                       input_cfg=os.path.join(working_dir, "work"), mc_args=self._mc_args)
        s.run()

        print("Output stream:")
        last_communicate = ""
        while s.status != Executable.FAILED_STATUS and s.status != Executable.FINISHED_STATUS:
            if s.communicate != last_communicate:
                last_communicate = s.communicate
                print(last_communicate)

        # read data, make python objects
        import glob
        from pymchelper.detector import Detector
        files = sorted(glob.glob(os.path.join(working_dir, "work/*.bdo")))
        results = {}
        for item in files:
            key = os.path.basename(item)
            value = Detector()
            value.read(item)
            results[key] = value

        # delete dir
        logger.info("Removing directory {:s}".format(working_dir))
        shutil.rmtree(working_dir)

        return results


class ParallelExecutor:
    def __init__(self):
        pass


class Monitor:
    def __init__(self, process, exec):
        self.process = process
        self.exec = exec

    def check_status(self):
        """
        Method which observe process p
        Raise ExecutorError
        """
        while True:
            line = self.process.stdout.readline()
            self.exec.last_stdout_line = line
            self.exec.output += line
            self.analyze_sh12a_line(line)
            if self.process.poll() is not None and line == '':
                break

        _stdout, stderr = self.process.communicate()  # stdout should be empty\
        assert (_stdout == '')  # just in case I was wrong about having stdout clear after above while
        self.exec.stderr = stderr  # Only one thing which I've receiver here was 'Note:...'
        self.exec._read_end_status()

    def check_if_sh12a_error_line(self, line):
        match = re.search('\*\*\* Error:', line)
        if match is not None:
            self.exec.status = self.exec.FAILED_STATUS
            raise ExecutorError(line)

    def check_if_sh12a_special_line(self, line):
        match = re.search('\*\*\*', line)
        if match is not None:
            self.exec.special_lines.append(line)
            self.check_if_sh12a_error_line(line)

    def analyze_sh12a_line(self, line):
        if self.exec.communicate is None:
            self.exec.communicate = "Initializing"
        self.check_if_sh12a_special_line(line)
        match = re.search('^ * Calculating for', line)
        match2 = re.search('particle no.', line)
        match3 = re.search('^ * Transport completed', line)
        if match is not None or match2 is not None or match3 is not None:
            self.exec.communicate = line
