from modules.runner.executor import Shield
from modules.runner.set_tmax0 import set_tmax0
from shutil import copytree, rmtree
import os


class ShieldsManager:
    """
    ShieldManager is class which manages currently observed shields. Now it is implemented as simple singleton.

    Attributes:
        executor - dictionary which contains pairs {id, Executor handle}
        shield_path - path to shield binary
        current_id - highest id of currently observed shields

    Class attributes:
        WORKSPACE_DIR - directory in which are created workspaces
        """


    _instance = None
    WORKSPACE_DIR = "workspaces/"

    def __new__(cls, *args, **kwargs):
        if ShieldsManager._instance is None:
            cls._instance = super(ShieldsManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'executors'):
            self.executors = {}
            self.current_id = 0

    def set_shield_path(self, shield_path):
        """Set shield binary path
        :param string shield_path   Path to shield binary"""
        self.shield_path = shield_path

    def start_shield(self, input_files, tmax0):
        """Start shield with given input files
        :param string input_files   path with input files for shield"""
        workspace_path = self._prepare_workspace(input_files)
        set_tmax0(tmax0, os.path.join(workspace_path, "beam.dat"))
        shield = Shield(workspace_path, self.shield_path)
        shield.tmax0 = tmax0
        shield.run()
        self.executors[self.current_id] = shield
        self.current_id += 1
        return shield

    def remove_shield(self, shield_id):
        """Remove shield from observed
        :param int shield_id    id of shield in self.executors"""
        del self.executors[shield_id]


    def _prepare_workspace(self, input_files):
        """Preparing and copying files to workspace"""
        workspace_path = ShieldsManager.WORKSPACE_DIR + str(self.current_id)
        try:
            rmtree(workspace_path)
        except FileNotFoundError:
            #it's ok that this directory does not exist
            pass

        copytree(input_files, workspace_path) #copy input files to workspace path
        return workspace_path