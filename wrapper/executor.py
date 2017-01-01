'''
Module allows to run shieldhit binary program, kill it, check current status, obtain current output (from stdout),
communicate from data analyzer, stdout, stderr and special lines from stdout (containing ***)
'''

import os
import threading
import re
from subprocess import Popen, PIPE
from modules.runner.executor_exceptions import ExecutorError, NotEnoughMemoryError, ProcessAlreadyStarted

MEM_INFO_FILE = "/proc/meminfo"


class Shield:
    """
    Class which is main wrapper to manage shieldhit binary program.
    Attributes:
        communicate - communicate which informs about sheldhit's work
        last_stdout_line - last read line from stdout
        output - read stdout from shieldhit's process
        status - status of running process
        special_lines - list of lines which contains ***
        stderr - read stderr from shieldhit's process after its end
        last_stdout_line - last read line from stdout

    How to start a proccess:
        s = Shield(folder)
        s.run()

    """
    RUNNING_STATUS = 'running'
    FINISHED_STATUS = 'finished'
    FAILED_STATUS = 'failed'
    TERMINATED_STATUS = 'terminated'
    NEEDED_MEMORY_KB = 1705524 #it's VSZ, should it be used or rather RSS? /in kB

    def __init__(self, input_files='', shield_path=''):
        """
        :param input_files: Folder which will be used as argument for shieldhit binary program - there should be data files
        :param shield_path: Path to shield-hit binary program
        for simulation in it
        """
        self._input_files = input_files
        self.shield_path = shield_path
        self._p = None
        self.status = None
        self.output = ""
        self.last_stdout_line = None
        self.stderr = None
        self.special_lines = []
        self.communicate = None

    def run(self):
        """
        Method starting shieldhit process and supervisor thread
        Raise:
            ProcessAlreadyStarted - if it's tried to run process while it's already running
            NotEnoughMemoryError - if there is not enough RAM to run process
        """
        if self.status == Shield.RUNNING_STATUS:
            raise ProcessAlreadyStarted

        #if get_available_memory() < Shield.NEEDED_MEMORY_KB:
        #    raise NotEnoughMemoryError

        self._clear_attributes()

        try:
            self._p = Popen([self.shield_path, self._input_files], stdout=PIPE, stderr=PIPE, universal_newlines=True)
        except (PermissionError, FileNotFoundError):
            raise ExecutorError("There is no shield in this path or there are problems with access to shield")

        self.status = Shield.RUNNING_STATUS

        self._supervisor = Supervisor(self._p, self)
        self._supervisor_thread = threading.Thread(target=self._supervisor.check_status, args=())
        self._supervisor_thread.start()

    def kill(self):
        if not self._p:
            raise ExecutorError('Firstly you have to run process')

        self._p.terminate()
        # is needed to finally kill defunct process
        os.waitpid(self._p.pid, 0)

        self.status = Shield.TERMINATED_STATUS
        self._p = None

    @property
    def pid(self):
        if self._p:
            return self._p.pid
        else:
            return None

    def _read_end_status(self):
        if self.status != Shield.TERMINATED_STATUS:
            s = self._p.returncode
            if s == 0:
                self.status = Shield.FINISHED_STATUS
            else:
                self.status = Shield.FAILED_STATUS

    def _clear_attributes(self):
        """
        Clear attributes
        Necessary in case run() is used twice
        """
        self._p = None
        self.status = None
        self.output = ""
        self.last_stdout_line = None
        self.stderr = None
        self.special_lines = []
        self.communicate = None

    @property
    def pid(self):
        if self._p:
            return self._p.pid
        else:
            return None


class Supervisor:
    def __init__(self, p, shield):
        self.p = p
        self.shield = shield

    def check_status(self):
        """
        Method which observe process p
        Raise ExecutorError
        """
        while True:
            line = self.p.stdout.readline()
            self.shield.last_stdout_line = line
            self.shield.output += line
            self.analyze_line(line)
            if self.p.poll() != None and line == '':
                break


        _stdout, stderr = self.p.communicate() #stdout should be empty\
        assert(_stdout == '')  #just in case I was wrong about having stdout clear after above while
        self.shield.stderr = stderr #Only one thing which I've receiver here was 'Note:...'
        #setting proper status in Shield class
        self.shield._read_end_status()

    def check_if_error_line(self, line):
        match = re.search('\*\*\* Error:', line)
        if match != None:
            self.shield.status = self.shield.FAILED_STATUS
            raise ExecutorError(line)

    def check_if_special_line(self, line):
        match = re.search('\*\*\*', line)
        if match != None:
            self.shield.special_lines.append(line)
            self.check_if_error_line(line)

    def analyze_line(self, line):
        if self.shield.communicate == None:
            self.shield.communicate = "Initializing"
        self.check_if_special_line(line)
        match = re.search('^ * Calculating for', line)
        match2 = re.search('particle no.', line)
        match3 = re.search('^ * Transport completed', line)
        if match != None or match2 != None or match3 != None:
            self.shield.communicate = line

def get_available_memory():
    """
    :return: available memory in kB (basing on MEM_INFO_FILE)
    """
    memory_info = open(MEM_INFO_FILE).read()
    match = re.search('(MemFree: *)(\d+)', memory_info)
    return int(match.groups()[1])

