import logging

from pymchelper.flair import Input
from pymchelper.flair.Input import Card

logger = logging.getLogger(__name__)


def create_input_header():
    # create empty input file object
    input_configuration = Input.Input()

    # add title
    input_configuration.addCard(Card("TITLE", extra="proton beam simulation"))

    # add default physics settings
    input_configuration.addCard(Card("DEFAULTS", what=["HADROTHE"], comment="default physics for hadron therapy"))

    # add beam characteristics, see http://www.fluka.org/fluka.php?id=man_onl&sub=12
    beam = Card("BEAM", comment="beam characteristics")
    beam.setSdum("PROTON")  # SDUM    = beam particle name.
    beam.setWhat(1, -0.12)  # WHAT(1) < 0.0 : average beam kinetic energy in GeV
    beam.setWhat(4, 2.0)  # WHAT(4) > 0.0 : If WHAT(6) > 0.0, beam width in x-direction in cm,
    # The beam profile is assumed to be rectangular
    beam.setWhat(5, 2.0)  # WHAT(5) > 0.0 : If WHAT(6) > 0.0, beam width in y-direction in cm.
    # The beam profile is assumed to be rectangular.
    input_configuration.addCard(beam)

    # add beam source position, see http://www.fluka.org/fluka.php?id=man_onl&sub=14
    beam_pos = Card("BEAMPOS", comment="beam source position")
    beam_pos.setWhat(1, 0.0)  # WHAT(1) = x-coordinate of the spot centre.
    beam_pos.setWhat(2, 0.0)  # WHAT(2) = y-coordinate of the spot centre.
    beam_pos.setWhat(3, -100.0)  # WHAT(3) = z-coordinate of the spot centre.
    input_configuration.addCard(beam_pos)

    return input_configuration


def fill_input_footer(input_configuration, no_of_particles=1000):

    # random number generator settings, see http://www.fluka.org/fluka.php?id=man_onl&sub=66
    rng_card = Card("RANDOMIZ")
    rng_card.setComment("random number generator settings")
    rng_card.setWhat(2, 137)  # Different numbers input as WHAT(2) will initialise different and independent
    # random number sequences, allowing the user to run several jobs in parallel for the same problem
    input_configuration.addCard(rng_card)

    # number of particles to simulate, see http://www.fluka.org/fluka.php?id=man_onl&sub=73
    start_card = Card("START")
    start_card.setComment("number of particles to simulate")
    start_card.setWhat(1, no_of_particles)  # WHAT(1) - maximum number of primary histories simulated in the run
    input_configuration.addCard(start_card)

    # end of input configuration http://www.fluka.org/fluka.php?id=man_onl&sub=76
    input_configuration.addCard(Card("STOP"))

    return input_configuration


def generate_fluka_file(output_filename, set_geometry, add_scoring):

    input_configuration = create_input_header()

    # set geometry, in separate function
    set_geometry(input_configuration)

    # add scoring, in separate function
    add_scoring(input_configuration)

    fill_input_footer(input_configuration, no_of_particles=1000)

    # write file to the disk
    input_configuration.write(output_filename)

    return input_configuration


def set_geometry(input_file):
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
    # 1. black body sphere, centered around (0,0,0), radius 10m
    blkbody_sph = Card("SPH", comment="black body sphere")
    blkbody_sph.setSdum("blkbody")  # SDUM - name of the body
    blkbody_sph.setWhat(1, 0.0)  # WHAT(1) - x-coordinate of the centre (in free format)
    blkbody_sph.setWhat(2, 0.0)  # WHAT(2) - y-coordinate of the centre (in free format)
    blkbody_sph.setWhat(3, 0.0)  # WHAT(3) - z-coordinate of the centre (in free format)
    blkbody_sph.setWhat(4, 10000.0)  # WHAT(4) - radius (in free format)
    input_file.addCard(blkbody_sph)

    # 2. air sphere, centered around (0,0,0), radius 1m
    air_sph = blkbody_sph.clone()  # see comments above
    air_sph.setSdum("air")
    air_sph.setWhat(4, 100.0)
    air_sph.setComment("air shpere")
    input_file.addCard(air_sph)

    # 3. target cylinder, bottom center at (0,0,0), height 10cm, radius 5cm, positioned along Z axis
    target_rcc = Card("RCC", comment="target cylinder")
    target_rcc.setSdum("target")  # SDUM - name of the body
    target_rcc.setWhat(1, 0.0)  # WHAT(1) - x-coordinate of the centre of circular plane, bottom (in free format)
    target_rcc.setWhat(2, 0.0)  # WHAT(2) - y-coordinate of the centre of circular plane, bottom (in free format)
    target_rcc.setWhat(3, 0.0)  # WHAT(3) - z-coordinate of the centre of circular plane, bottom (in free format)
    target_rcc.setWhat(4, 0.0)  # WHAT(4) - x-coordinate of the height vector (in free format)
    target_rcc.setWhat(5, 0.0)  # WHAT(5) - y-coordinate of the height vector (in free format)
    target_rcc.setWhat(6, 10.0)  # WHAT(6) - z-coordinate of the height vector (in free format)
    target_rcc.setWhat(7, 5.0)  # WHAT(7) - radius (in free format)
    input_file.addCard(target_rcc)

    # end of body region
    input_file.addCard(Card("END"))

    # list of regions, see http://www.fluka.org/fluka.php?id=man_onl&sub=94
    # 1. outer black body region
    blk_body_zone = Card("REGION")
    blk_body_zone.setComment("outer black body region")
    blk_body_zone.setSdum("Z_BBODY")  # SDUM - name of the region
    blk_body_zone.addZone('+blkbody -air')  # logical formula
    input_file.addCard(blk_body_zone)

    # 2. inner air region
    air_zone = Card("REGION")
    air_zone.setComment("inner air region")
    air_zone.setSdum("Z_AIR")
    air_zone.addZone('+air -target')
    input_file.addCard(air_zone)

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
    air_mat.setWhat(1, 'AIR')
    air_mat.setWhat(2, air_zone.sdum())
    input_file.addCard(air_mat)

    target_mat = Card("ASSIGNMA")  # see comments above
    target_mat.setWhat(1, 'WATER')
    target_mat.setWhat(2, target_zone.sdum())
    input_file.addCard(target_mat)
