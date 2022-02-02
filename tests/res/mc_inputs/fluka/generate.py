import sys
from itertools import product

from pymchelper.flair import Input
from pymchelper.flair.Input import Card
from pymchelper.shieldhit.detector.geometry import CarthesianMesh


def generate_fluka_file(output_filename: str):
    """
    Fluka input file is saved in the default format (as Flair saves it), namely:
      - fixed format is used everywhere, except:
      - free format for geometry, forced by COMBNAME paramater in GEOBEGIN card
      - names instead of numbers are used as identifies of particles, materials and regions

    :param output_filename: output filename
    """

    # create empty input file object
    input_configuration = Input.Input()

    # add title
    input_configuration.addCard(Card("TITLE", extra="proton beam simulation"))

    # add default physics settings
    input_configuration.addCard(Card("DEFAULTS", what=["HADROTHE"], comment="default physics for hadron therapy"))

    # add beam characteristics, see http://www.fluka.org/fluka.php?id=man_onl&sub=12
    beam = Card("BEAM", comment="beam characteristics")
    beam.setSdum("PROTON")  # SDUM    = beam particle name.
    beam.setWhat(1, -0.150)  # WHAT(1) < 0.0 : average beam kinetic energy in GeV
    beam.setWhat(2, 0.)  # beam momentum spread
    beam.setWhat(3, 0.)  # beam divergence
    beam.setWhat(4, 0.)
    beam.setWhat(5, 0.)
    beam.setWhat(6, 0.)
    input_configuration.addCard(beam)

    # add beam source position, see http://www.fluka.org/fluka.php?id=man_onl&sub=14
    beam_pos = Card("BEAMPOS", comment="beam source position")
    beam_pos.setWhat(1, 0.0)  # WHAT(1) = x-coordinate of the spot centre.
    beam_pos.setWhat(2, 0.0)  # WHAT(2) = y-coordinate of the spot centre.
    beam_pos.setWhat(3, 0.0)  # WHAT(3) = z-coordinate of the spot centre.
    beam_pos.setWhat(4, 0.0)
    beam_pos.setWhat(5, 0.0)
    input_configuration.addCard(beam_pos)

    # set geometry, in separate function
    set_geometry(input_configuration)

    # add scoring, in separate function
    add_scoring(input_configuration)

    # random number generator settings, see http://www.fluka.org/fluka.php?id=man_onl&sub=66
    rng_card = Card("RANDOMIZ")
    rng_card.setComment("random number generator settings")
    rng_card.setWhat(1, 1.0)  # logical file unit from which to read the seeds.
    rng_card.setWhat(2, 1)  # Different numbers input as WHAT(2) will initialise different and independent
    # random number sequences, allowing the user to run several jobs in parallel for the same problem
    input_configuration.addCard(rng_card)

    # number of particles to simulate, see http://www.fluka.org/fluka.php?id=man_onl&sub=73
    start_card = Card("START")
    start_card.setComment("number of particles to simulate")
    start_card.setWhat(1, 100000)  # WHAT(1) - maximum number of primary histories simulated in the run
    input_configuration.addCard(start_card)

    # end of input configuration http://www.fluka.org/fluka.php?id=man_onl&sub=76
    input_configuration.addCard(Card("STOP"))

    # write file to the disk
    input_configuration.write(output_filename)

    return input_configuration


def set_geometry(input_file: Input.Input):
    """
    Add simple geometry, consisting of water target, surrounded with air.
    :param input_file: Fluka input file object, will be modified
    :return:
    """

    # geometry description starts here http://www.fluka.org/fluka.php?id=man_onl&sub=38
    geo_begin = Card("GEOBEGIN", comment="geometry description starts here")
    geo_begin.setSdum("COMBNAME")  # SDUM = COMBNAME  : Combinatorial geometry is used in free format,
    # and names can be used instead of body and region numbers
    input_file.addCard(geo_begin)

    # list of bodies, see http://www.fluka.org/fluka.php?id=man_onl&sub=94
    # 1. black body box
    black_body_card = Card("RPP", comment="black body box")
    black_body_card.setSdum("blkbody")  # SDUM - name of the body
    black_body_card.setWhat(1, -7.0)  # WHAT(1) - X_min
    black_body_card.setWhat(2, 7.0)  # WHAT(2) - X_max
    black_body_card.setWhat(3, -7.0)  # WHAT(3) - Y_min
    black_body_card.setWhat(4, 7.0)  # WHAT(4) - Y_max
    black_body_card.setWhat(5, -2.0)  # WHAT(5) - Z_min
    black_body_card.setWhat(6, 22.0)  # WHAT(6) - Z_max
    input_file.addCard(black_body_card)

    # 2. air box
    vacuum_body_card = black_body_card.clone()  # see comments above
    vacuum_body_card.setSdum("vacuum")
    vacuum_body_card.setWhat(1, -6.0)  # WHAT(1) - X_min
    vacuum_body_card.setWhat(2, 6.0)  # WHAT(2) - X_max
    vacuum_body_card.setWhat(3, -6.0)  # WHAT(3) - Y_min
    vacuum_body_card.setWhat(4, 6.0)  # WHAT(4) - Y_max
    vacuum_body_card.setWhat(5, -1.0)  # WHAT(5) - Z_min
    vacuum_body_card.setWhat(6, 21.0)  # WHAT(6) - Z_max
    vacuum_body_card.setComment("vacuum box")
    input_file.addCard(vacuum_body_card)

    # 3. target water phantom
    phantom_body_card = Card("RPP", comment="water phantom")
    phantom_body_card.setSdum("target")  # SDUM - name of the body
    phantom_body_card.setWhat(1, -5.0)  # WHAT(1) - X_min
    phantom_body_card.setWhat(2, 5.0)  # WHAT(2) - X_max
    phantom_body_card.setWhat(3, -5.0)  # WHAT(3) - Y_min
    phantom_body_card.setWhat(4, 5.0)  # WHAT(4) - Y_max
    phantom_body_card.setWhat(5, 0.0)  # WHAT(5) - Z_min
    phantom_body_card.setWhat(6, 20.0)  # WHAT(6) - Z_max
    input_file.addCard(phantom_body_card)

    # end of body region
    input_file.addCard(Card("END"))

    # list of regions, see http://www.fluka.org/fluka.php?id=man_onl&sub=94
    # 1. outer black body region
    blk_body_zone = Card("REGION")
    blk_body_zone.setComment("outer black body region")
    blk_body_zone.setSdum("Z_BBODY")  # SDUM - name of the region
    blk_body_zone.addZone('+blkbody -vacuum')  # logical formula
    input_file.addCard(blk_body_zone)

    # 2. inner air region
    vacuum_zone = Card("REGION")
    vacuum_zone.setComment("inner vacuum region")
    vacuum_zone.setSdum("Z_VACUUM")
    vacuum_zone.addZone('+vacuum -target')
    input_file.addCard(vacuum_zone)

    # 3. target region
    target_zone = Card("REGION")
    target_zone.setComment("target region")
    target_zone.setSdum("Z_TARGET")
    target_zone.addZone('+target')
    input_file.addCard(target_zone)

    # end of target region
    input_file.addCard(Card("END"))

    # geometry description ends here http://www.fluka.org/fluka.php?id=man_onl&sub=39
    geo_end = Card("GEOEND", comment="geometry description ends here")
    input_file.addCard(geo_end)

    # material assignment, see http://www.fluka.org/fluka.php?id=man_onl&sub=10
    blk_body_mat = Card("ASSIGNMA")
    blk_body_mat.setWhat(1, 'BLCKHOLE')  # WHAT(1) - material index, or material name
    blk_body_mat.setWhat(2, blk_body_zone.sdum())  # WHAT(2) - lower bound (or name corresponding to it) of the region
    # indices with material index equal or corresponding to WHAT(1).
    # upper bound is set to WHAT(2) by default
    input_file.addCard(blk_body_mat)

    air_mat = Card("ASSIGNMA")  # see comments above
    air_mat.setWhat(1, 'VACUUM')
    air_mat.setWhat(2, vacuum_zone.sdum())
    input_file.addCard(air_mat)

    target_mat = Card("ASSIGNMA")  # see comments above
    target_mat.setWhat(1, 'WATER')
    target_mat.setWhat(2, target_zone.sdum())
    input_file.addCard(target_mat)


def add_scoring(input_file: Input.Input):
    """
    :param input_file: Fluka input_file object, will be modified
    :return:
    """

    # scoring, see http://www.fluka.org/fluka.php?id=man_onl&sub=84
    card1 = Card("USRBIN")
    card1.setWhat(1, 10.0)  # WHAT(1) - type of binning selected (0.0 : Mesh Cartesian, no sym.)
    card2 = Card("USRBIN")
    card2.setSdum("&")  # continuation card

    # for list of all possible generalized particles, see: http://www.fluka.org/fluka.php?id=man_onl&sub=7
    card1.setComment("scoring dose")
    card1.setSdum("dose")  # SDUM - identifying the binning detector
    card1.setWhat(2, "DOSE")  # WHAT(2) - particle (or particle family) type to be scored
    card1.setWhat(3, -21)  # WHAT(3) - output unit (> 0.0 : formatted data,  < 0.0 : unformatted data)

    # Define scoring mesh
    card1.setWhat(4, 5.)  # WHAT(4) - For Cartesian binning: Xmax
    card1.setWhat(5, 5.)  # WHAT(5) - For Cartesian binning: Ymax
    card1.setWhat(6, 20.)  # WHAT(6) - For Cartesian binning: Zmax
    card2.setWhat(1, -5.)  # WHAT(1) - For Cartesian binning: Xmin
    card2.setWhat(2, -5.)  # WHAT(2) - For Cartesian binning: Ymin
    card2.setWhat(3, 0.)  # WHAT(3) - For Cartesian binning: Zmin
    card2.setWhat(4, 1)  # WHAT(4) - For Cartesian binning: number of X bins
    card2.setWhat(5, 1)  # WHAT(5) - For Cartesian binning: number of Y bins
    card2.setWhat(6, 100)  # WHAT(6) - For Cartesian binning: number of Z bins

    # finally add generated cards to input structure
    card1.appendWhats(card2.whats()[1:])
    input_file.addCard(card1)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    generate_fluka_file("fluka.inp")


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))