from enum import IntEnum


class SHDetType(IntEnum):
    unknown = 0
    energy = 1
    fluence = 2
    crossflu = 3
    letflu = 4
    dose = 5
    dlet = 6
    tlet = 7
    avg_energy = 8
    avg_beta = 9
    material = 10
    alanine = 13
    counter = 14
    pet = 15
    dletg = 16
    tletg = 17
    zone = 18
    medium = 19
    rho = 20
    let = 120  # for differential scoring
    angle = 121  # for differential scoring

    def __str__(self):
        return self.name.upper().replace('_', '-')
