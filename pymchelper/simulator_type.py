from enum import IntEnum
from typing import List, Optional


class SimulatorType(IntEnum):
    """Type of the MC simulator: SHIELD-HIT12A, TOPAS or FLUKA"""

    shieldhit = 1
    topas = 2
    fluka = 3

    @classmethod
    @property
    def names(cls) -> List[str]:
        """Return list of available simulators"""
        return [s.name for s in SimulatorType]

    @staticmethod
    def from_name(name: str) -> Optional['SimulatorType']:
        """Return simulator type from its name"""
        try:
            return SimulatorType[name]
        except KeyError:
            return None
