import sys
from itertools import product

from pymchelper.flair import Input
from pymchelper.flair.Input import Card
from pymchelper.shieldhit.detector.geometry import CarthesianMesh


def generate_fluka_file(output_filename):
    """
    Compose programatically fl_sim.inp Fluka input file
    with many combinations of detector and mesh types.

    Fluka input file is saved in the default format (as Flair saves it), namely:
      - fixed format is used everywhere, except:
      - free format for geometry, forced by COMBNAME paramater in GEOBEGIN card
      - names instead of numbers are used as identifies of particles, materials and regions

    :param output_filename: output filename
    :return: generated Fluka object
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
    beam.setWhat(1, -0.06)  # WHAT(1) < 0.0 : average beam kinetic energy in GeV
    beam.setWhat(4, 2.0)  # WHAT(4) > 0.0 : If WHAT(6) > 0.0, beam width in x-direction in cm,
    # The beam profile is assumed to be rectangular
    beam.setWhat(5, 2.0)  # WHAT(5) > 0.0 : If WHAT(6) > 0.0, beam width in y-direction in cm.
    # The beam profile is assumed to be rectangular.
    input_configuration.addCard(Card("BEAM", what=["PROTON", -0.06, 0.0, 0.0, -2.0, -2.0], comment="beam source"))

    # add beam source position, see http://www.fluka.org/fluka.php?id=man_onl&sub=14
    beam_pos = Card("BEAMPOS", comment="beam source position")
    beam_pos.setWhat(1, 0.0)  # WHAT(1) = x-coordinate of the spot centre.
    beam_pos.setWhat(2, 0.0)  # WHAT(2) = y-coordinate of the spot centre.
    beam_pos.setWhat(3, -100.0)  # WHAT(3) = z-coordinate of the spot centre.
    input_configuration.addCard(beam_pos)

    # set geometry, in separate function
    set_geometry(input_configuration)

    # add scoring, in separate function
    add_scoring(input_configuration)

    # random number generator settings, see http://www.fluka.org/fluka.php?id=man_onl&sub=66
    rng_card = Card("RANDOMIZ")
    rng_card.setComment("random number generator settings")
    rng_card.setWhat(2, 137)  # Different numbers input as WHAT(2) will initialise different and independent
    # random number sequences, allowing the user to run several jobs in parallel for the same problem
    input_configuration.addCard(rng_card)

    # number of particles to simulate, see http://www.fluka.org/fluka.php?id=man_onl&sub=73
    start_card = Card("START")
    start_card.setComment("number of particles to simulate")
    start_card.setWhat(1, 1000)  # WHAT(1) - maximum number of primary histories simulated in the run
    input_configuration.addCard(start_card)

    # end of input configuration http://www.fluka.org/fluka.php?id=man_onl&sub=76
    input_configuration.addCard(Card("STOP"))

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


def add_scoring(input_file):
    """
    Add scoring of deposited energy and neutron fluence on 4 different mesh types (8 scorers in total)
    :param input_file: Fluka input_file object, will be modified
    :return:
    """

    # Dictionary of scoring type (generalized particle)
    # keys will be used as parts of output filenames, this is why they are short
    # for list of all possible generalized particles, see: http://www.fluka.org/fluka.php?id=man_onl&sub=7
    det_types = {"en": "ENERGY", "n": "NEUTRON"}

    # Define 4 different scoring meshes (1D and 2D), using pymchelper classes
    msh_z = CarthesianMesh()
    msh_z.set_axis(axis_no=0, start=-0.5, stop=0.5, nbins=1)
    msh_z.set_axis(axis_no=1, start=-0.5, stop=0.5, nbins=1)
    msh_z.set_axis(axis_no=2, start=0.0, stop=5.0, nbins=500)

    msh_xy = CarthesianMesh()
    msh_xy.set_axis(axis_no=0, start=-5.0, stop=5.0, nbins=500)
    msh_xy.set_axis(axis_no=1, start=-5.0, stop=5.0, nbins=500)
    msh_xy.set_axis(axis_no=2, start=2.8, stop=2.9, nbins=1)

    msh_yz = CarthesianMesh()
    msh_yz.set_axis(axis_no=0, start=-0.1, stop=0.1, nbins=1)
    msh_yz.set_axis(axis_no=1, start=-5.0, stop=5.0, nbins=500)
    msh_yz.set_axis(axis_no=2, start=0.0, stop=5.0, nbins=500)

    msh_zx = CarthesianMesh()
    msh_zx.set_axis(axis_no=0, start=-5.0, stop=5.0, nbins=500)
    msh_zx.set_axis(axis_no=1, start=-0.1, stop=0.1, nbins=1)
    msh_zx.set_axis(axis_no=2, start=0.0, stop=5.0, nbins=500)

    mesh_types = {"z": msh_z, "xy": msh_xy, "yz": msh_yz, "zx": msh_zx}

    # Fluka is using concept of output unit numbers, this is starting number,
    # for each new scorer will be decreased by one
    output_unit = -21

    # scoring, see http://www.fluka.org/fluka.php?id=man_onl&sub=84
    # template cards for USRBIN scorers:
    usrbin_card1 = Card("USRBIN")
    usrbin_card1.setWhat(1, 0.0)  # WHAT(1) - type of binning selected (0.0 : Mesh Cartesian, no sym.)
    usrbin_card2 = Card("USRBIN")
    usrbin_card2.setSdum("&")  # continuation card

    # loop over all possible detectors and meshes
    for det_type, mesh_type in product(det_types.keys(), mesh_types.keys()):

        # make copies of template cards
        card1 = usrbin_card1.clone()
        card2 = usrbin_card2.clone()

        # generate comment
        card1.setComment("scoring {:s} on mesh {:s}".format(det_types[det_type], mesh_type))
        card1.setSdum("{:s}_{:s}".format(det_type, mesh_type))  # SDUM - identifying the binning detector
        card1.setWhat(2, det_types[det_type])  # WHAT(2) - particle (or particle family) type to be scored
        card1.setWhat(3, output_unit)  # WHAT(3) - output unit (> 0.0 : formatted data,  < 0.0 : unformatted data)

        msh = mesh_types[mesh_type]
        card1.setWhat(4, msh.axis[0].stop)  # WHAT(4) - For Cartesian binning: Xmax
        card1.setWhat(5, msh.axis[1].stop)  # WHAT(5) - For Cartesian binning: Ymax
        card1.setWhat(6, msh.axis[2].stop)  # WHAT(6) - For Cartesian binning: Zmax
        card2.setWhat(1, msh.axis[0].start)  # WHAT(1) - For Cartesian binning: Xmin
        card2.setWhat(2, msh.axis[1].start)  # WHAT(2) - For Cartesian binning: Ymin
        card2.setWhat(3, msh.axis[2].start)  # WHAT(3) - For Cartesian binning: Zmin
        card2.setWhat(4, msh.axis[0].nbins)  # WHAT(4) - For Cartesian binning: number of X bins
        card2.setWhat(5, msh.axis[1].nbins)  # WHAT(5) - For Cartesian binning: number of Y bins
        card2.setWhat(6, msh.axis[2].nbins)  # WHAT(6) - For Cartesian binning: number of Z bins
        output_unit -= 1

        # finally add generated cards to input structure
        input_file.addCard(card1)
        card1.appendWhats(card2.whats()[1:])


def main(args=sys.argv[1:]):

    generate_fluka_file("fl_sim.inp")

    # fl_sim.inp file should have following content:
    # TITLE
    # proton beam simulation
    # * default physics settings for hadron therapy
    # DEFAULTS                                                              HADROTHE
    # * beam source
    # BEAM           -0.06       0.0       0.0      -2.0      -2.0          PROTON
    # * beam source position
    # BEAMPOS          0.0       0.0    -100.0
    # * geometry description starts here
    # GEOBEGIN                                                              COMBNAME
    #     0    0
    # * black body sphere
    # SPH blkbody    0.0 0.0 0.0 10000.0
    # * air shpere
    # SPH air        0.0 0.0 0.0 100.0
    # * target cylinder
    # RCC target     0.0 0.0 0.0 0.0 0.0 10.0 5.0
    # END
    # * outer black body region
    # Z_BBODY      5 +blkbody -air
    # * inner air region
    # Z_AIR        5 +air -target
    # * target region
    # Z_TARGET     5 +target
    # END
    # GEOEND
    # ASSIGNMA    BLCKHOLE   Z_BBODY
    # ASSIGNMA         AIR     Z_AIR
    # ASSIGNMA       WATER  Z_TARGET
    # * scoring NEUTRON on mesh z
    # USRBIN           0.0   NEUTRON       -21       0.5       0.5       5.0n_z
    # USRBIN          -0.5      -0.5       0.0         1         1       500&
    # * scoring NEUTRON on mesh yz
    # USRBIN           0.0   NEUTRON       -22       0.1       5.0       5.0n_yz
    # USRBIN          -0.1      -5.0       0.0         1       500       500&
    # * scoring NEUTRON on mesh xy
    # USRBIN           0.0   NEUTRON       -23       5.0       5.0       2.9n_xy
    # USRBIN          -5.0      -5.0       2.8       500       500         1&
    # * scoring NEUTRON on mesh zx
    # USRBIN           0.0   NEUTRON       -24       5.0       0.1       5.0n_zx
    # USRBIN          -5.0      -0.1       0.0       500         1       500&
    # * scoring ENERGY on mesh z
    # USRBIN           0.0    ENERGY       -25       0.5       0.5       5.0en_z
    # USRBIN          -0.5      -0.5       0.0         1         1       500&
    # * scoring ENERGY on mesh yz
    # USRBIN           0.0    ENERGY       -26       0.1       5.0       5.0en_yz
    # USRBIN          -0.1      -5.0       0.0         1       500       500&
    # * scoring ENERGY on mesh xy
    # USRBIN           0.0    ENERGY       -27       5.0       5.0       2.9en_xy
    # USRBIN          -5.0      -5.0       2.8       500       500         1&
    # * scoring ENERGY on mesh zx
    # USRBIN           0.0    ENERGY       -28       5.0       0.1       5.0en_zx
    # USRBIN          -5.0      -0.1       0.0       500         1       500&
    # * random number generator settings
    # RANDOMIZ                   137
    # * number of particles to simulate
    # START           1000
    # STOP


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
