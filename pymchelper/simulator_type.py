from enum import IntEnum

class SimulatorType(IntEnum):
    """
    Type of the MC simulator: SHIELD-HIT12A, TOPAS or FLUKA
    """
    shieldhit = 1
    topas = 2
    fluka = 3