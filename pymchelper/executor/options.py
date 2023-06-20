"""Options for simulation."""

from dataclasses import dataclass
from typing import Optional

from pymchelper.executor.types import PathLike
from pymchelper.simulator_type import SimulatorType


@dataclass(repr=True)
class SimulationOptions:
    """This class is responsible for keeping settings of simulation.

    Attributes:
        input_path: path to input file or directory
        simulator_type: type of simulator (shieldhit, topas or fluka) :class:`SimulatorType`
        simulator_exec_path: path to executable file of simulator
        cmdline_opts: extra options for simulator
    """

    input_path: PathLike
    simulator_type: Optional[SimulatorType] = None
    simulator_exec_path: Optional[PathLike] = None
    cmdline_opts: Optional[str] = None

    def __dict__(self):
        """Return dictionary representation of the object."""
        return {
            'input_path': self.input_path,
            'simulator_type': self.simulator_type,
            'simulator_exec_path': self.simulator_exec_path,
            'cmdline_opts': self.cmdline_opts
        }
