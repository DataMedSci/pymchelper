from enum import IntEnum


class SHDetType(IntEnum):
    """
    List of available detector types below is based on IDET(5,*) in detect.f and sh_scoredef.h in SHIELD-HIT12A.
    If new detectors are added, class SHEstimator in estimator.py should also be updated.
    """

    none = 0
    energy = 1
    fluence = 2
    crossflu = 3
    letflu = 4

    dose = 5
    dlet = 6
    tlet = 7
    avg_energy = 8
    avg_beta = 9

    spc = 10
    material = 11
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
    flu_neqv = 24

    angle = 25
    trace = 26
    kinetic_energy = 27
    energy_nuc = 28
    energy_amu = 29

    a = 30
    amass = 31
    amu = 32
    gen = 33
    id = 34

    dedx = 35
    mass_dedx = 36
    track_length = 37
    nkerma = 38
    dose_gy = 39

    dose_eqv = 40
    eqv_dose = 41
    user1 = 42
    user2 = 43
    n_eqv_dose = 44  # Neutron equivalent dose, ICRP 103 protection quantity.

    z2beta2 = 45
    dose_av_z2beta2 = 46
    track_av_z2beta2 = 47
    dose_av_q = 48
    track_av_q = 49

    z = 50
    zeff = 51
    zeff2beta2 = 52
    tzeff2beta2 = 53
    dzeff2beta2 = 54

    count = 55  # simple counter, not normalized to per primary particle
    norm_count_point = 56  # score_point counter, normalized per primary particle
    count_point = 57  # score_point counter, not normalized per primary particle
    moca_yf = 58  # frequency-averaged lineal energy from Moca
    moca_yd = 59  # dose-averaged lineal energy from Moca

    q_eff = 60  # Effective Q, Q_eff, aka zeff2beta2
    dq_eff = 61  # Dose-averaged Q_eff
    tq_eff = 62  # Track-averaged Q_eff

    let_bdo2016 = 120  # for differential scoring
    angle_bdo2016 = 121  # for differential scoring
    dose_gy_bdo2016 = 205
    alanine_gy_bdo2016 = 213

    invalid = 32767

    def __str__(self):
        return self.name.upper().replace('_', '-')
