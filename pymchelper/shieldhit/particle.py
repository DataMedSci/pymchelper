from enum import IntEnum


class SHParticleType(IntEnum):
    all = -1
    unknown = 0
    neutron = 1
    proton = 2
    pi_minus = 3
    pi_plus = 4
    pi_zero = 5
    anti_neutron = 6
    anti_proton = 7
    kaon_minus = 8
    kaon_plus = 9
    kaon_zero = 10
    kaon_tilde = 11
    gamma = 12
    electron = 13
    positron = 14
    muon_minus = 15
    muon_plus = 16
    neutrino_e = 17
    anti_neutrino_e = 18
    neutrino_mu = 19
    anti_neutrino_mu = 20
    deuteron = 21
    triton = 22
    helium_3 = 23
    helium_4 = 24
    heavy_ion = 25

    def __str__(self):
        return self.name.replace('_', '-')


class SHHeavyIonType:
    particle_type = SHParticleType.heavy_ion

    def __init__(self):
        self.a = 0
        self.z = 0

    def __str__(self):
        result = str(self.particle_type)
        result += "_{:d}".format(self.z)
        result += "^{:d}".format(self.a)
        return result
