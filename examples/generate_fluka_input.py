import sys
# from itertools import product

# import necessary code pieces from pymchelper
# from pymchelper.shieldhit.detector.detector_type import SHDetType
# from pymchelper.shieldhit.detector.estimator import SHEstimator
# from pymchelper.shieldhit.detector.estimator_type import SHGeoType
# from pymchelper.shieldhit.detector.fortran_card import EstimatorWriter, CardLine
# from pymchelper.shieldhit.detector.geometry import CarthesianMesh
# from pymchelper.shieldhit.particle import SHParticleType
from pymchelper.flair import Input
from pymchelper.flair.Input import Card


def main(args=sys.argv[1:]):
    """
    Compose programatically fl_sim.inp Fluka input file
    with fixed mesh and many combinations of detector and particle type.
    :param args: part of sys.argv, used here to simplify automated testing
    :return: None
    """

    # # create empty estimator object
    # estimator = SHEstimator()
    #
    # # create carthesian mesh
    # # it is done once and in single place
    # # editing in manually in detect.dat file would require changes in many lines,
    # # for every combination of particle and detector type, making it error prone
    # estimator.estimator = SHGeoType.msh
    # estimator.geometry = CarthesianMesh()
    # estimator.geometry.set_axis(axis_no=0, start=-5.0, stop=5.0, nbins=1)
    # estimator.geometry.set_axis(axis_no=1, start=-5.0, stop=5.0, nbins=1)
    # estimator.geometry.set_axis(axis_no=2, start=0.0, stop=30.0, nbins=300)
    #
    # # possible detector types and associated names
    # det_types = {SHDetType.energy: "en", SHDetType.fluence: "fl"}
    #
    # # possible particle types and associated names
    # particle_types = {SHParticleType.all: "all", SHParticleType.proton: "p", SHParticleType.neutron: "n"}
    #
    # # open detector.dat file for writing
    # with open("detect.dat", "w") as f:
    #     f.write(CardLine.credits + "\n")
    #
    #     # loop over all combinations of detector and particle types
    #     # output filename will be composed from associated detector and particle names
    #     for dt, pt in product(det_types.keys(), particle_types.keys()):
    #         estimator.detector_type = dt
    #         estimator.particle_type = pt
    #         estimator.filename = det_types[dt] + "_" + particle_types[pt]
    #         text = EstimatorWriter.get_text(estimator, add_comment=True)
    #         f.write(text)
    #     f.write(CardLine.comment + "\n")

    Input.init()

    # create empty input file
    input = Input.Input()

    # add title
    input.addCard(Card("TITLE", comment="proton simulation"))

    # add default physics settings
    input.addCard(Card("DEFAULTS", what=["HADRONTHE"], comment="default physics settings"))

    # add beam characteristics, see http://www.fluka.org/fluka.php?id=man_onl&sub=12
    beam = Card("BEAM", comment="beam characteristics")
    beam.setSdum("PROTON")  # SDUM    = beam particle name.
    beam.setWhat(1, -0.06)  # WHAT(1) < 0.0 : average beam kinetic energy in GeV
    beam.setWhat(4, 2.0)  # WHAT(4) > 0.0 : If WHAT(6) > 0.0, beam width in x-direction in cm,
    # The beam profile is assumed to be rectangular
    beam.setWhat(5, 2.0)  # WHAT(5) > 0.0 : If WHAT(6) > 0.0, beam width in y-direction in cm.
    # The beam profile is assumed to be rectangular.
    input.addCard(Card("BEAM", what=["PROTON", -0.06, 0.0, 0.0, -2.0, -2.0], comment="beam source"))

    # add beam source position, see http://www.fluka.org/fluka.php?id=man_onl&sub=14
    beam_pos = Card("BEAMPOS", comment="beam source position")
    beam_pos.setWhat(1, 0.0)  # WHAT(1) = x-coordinate of the spot centre.
    beam_pos.setWhat(2, 0.0)  # WHAT(2) = y-coordinate of the spot centre.
    beam_pos.setWhat(3, -100.0)  # WHAT(3) = z-coordinate of the spot centre.
    input.addCard(beam_pos)

    # geometry description starts here http://www.fluka.org/fluka.php?id=man_onl&sub=38
    geo_begin = Card("GEOBEGIN", comment="geometry description starts here")
    geo_begin.setSdum("COMBNAME")  # SDUM = COMBNAME  : Combinatorial geometry is used in free format,
    # and names can be used instead of body and region numbers
    input.addCard(geo_begin)

    blkbody_sph = Card("SPH", comment="black body sphere")
    blkbody_sph.setSdum("blkbody")
    blkbody_sph.setWhat(1, 0.0)
    blkbody_sph.setWhat(2, 0.0)
    blkbody_sph.setWhat(3, 0.0)
    blkbody_sph.setWhat(4, 10000.0)
    input.addCard(blkbody_sph)

    air_sph = blkbody_sph.clone()
    air_sph.setSdum("air")
    air_sph.setWhat(4, 100.0)
    air_sph.setComment("air shpere")
    input.addCard(air_sph)

    target_rcc = Card("RCC", comment="target cylinder")
    target_rcc.setSdum("target")
    target_rcc.setWhat(1, 0.0)
    target_rcc.setWhat(2, 0.0)
    target_rcc.setWhat(3, 0.0)
    target_rcc.setWhat(4, 0.0)
    target_rcc.setWhat(5, 0.0)
    target_rcc.setWhat(6, 10.0)
    target_rcc.setWhat(7, 5.0)
    input.addCard(target_rcc)

    input.addCard(Card("END"))

    blk_body_zone = Card("REGION")
    blk_body_zone.setSdum("z_bbody")
    blk_body_zone.addZone('+blkbody -air')
    input.addCard(blk_body_zone)

    air_zone = Card("REGION")
    air_zone.setSdum("z_air")
    air_zone.addZone('+air -target')
    input.addCard(air_zone)

    target_zone = Card("REGION")
    target_zone.setSdum("z_target")
    target_zone.addZone('+target')
    input.addCard(target_zone)

    # http://www.fluka.org/fluka.php?id=man_onl&sub=10
    blk_body_mat = Card("ASSIGNMA")
    blk_body_mat.setWhat(1, 'BLCKHOLE')
    blk_body_mat.setWhat(2, blk_body_zone.sdum())
    input.addCard(blk_body_mat)

    air_mat = Card("ASSIGNMA")
    air_mat.setWhat(1, 'AIR')
    air_mat.setWhat(2, air_zone.sdum())
    input.addCard(air_mat)

    target_mat = Card("ASSIGNMA")
    target_mat.setWhat(1, 'WATER')
    target_mat.setWhat(2, target_zone.sdum())
    input.addCard(target_mat)

    usrbin1 = Card("USRBIN")
    usrbin1.setSdum('dose_z_1')
    input.addCard(usrbin1)

    # http://www.fluka.org/fluka.php?id=man_onl&sub=66
    random = Card("RANDOMIZ")
    random.setWhat(2, 137)
    input.addCard(random)

    # http://www.fluka.org/fluka.php?id=man_onl&sub=73
    start = Card("START")
    start.setWhat(1, 1000)
    input.addCard(start)

    input.write("fl_sim.inp")

    # fl_sim.inp file should have following content:
    # TODO


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
