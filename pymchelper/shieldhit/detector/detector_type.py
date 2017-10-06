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
    ddd = 12
    alanine = 13
    counter = 14
    pet = 15
    dletg = 16
    tletg = 17
    zone = 18
    medium = 19
    rho = 20
    q = 21
    flu_char = 22
    flu_neut = 23
    let = 120  # for differential scoring
    angle = 121  # for differential scoring
    dose_gy = 205
    alanine_gy = 213

    def __str__(self):
        return self.name.upper().replace('_', '-')
