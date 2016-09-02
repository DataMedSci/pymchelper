from itertools import product

from pymchelper.flair.Input import Card


def add_scoring_filters_track(input_file):
    det_types = {"p": "PROTON",
                 "n": "NEUTRON",
                 "e": "ELECTRON",
                 "ph": "PHOTON",
                 "ap": "ALL-PART",
                 "ac": "ALL-CHAR",
                 "an": "ALL-NEUT",
                 "nuc": "NUCLEONS",
                 "e": "ENERGY",
                 "bp": "BEAMPART" }

    mesh_types = {"1": 1}

    # Fluka is using concept of output unit numbers, this is starting number,
    # for each new scorer will be decreased by one
    output_unit = -21

    # scoring, see http://www.fluka.org/fluka.php?id=man_onl&sub=89
    # template cards for USRTRACK scorers:
    usrbin_card1 = Card("USRTRACK")
    usrbin_card1.setWhat(1, 0.0)  # WHAT(1) - type of binning selected (0.0 : Mesh Cartesian, no sym.)
    usrbin_card2 = Card("USRTRACK")
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
        #
        # msh = mesh_types[mesh_type]
        # card1.setWhat(4, msh.axis[0].stop)  # WHAT(4) - For Cartesian binning: Xmax
        # card1.setWhat(5, msh.axis[1].stop)  # WHAT(5) - For Cartesian binning: Ymax
        # card1.setWhat(6, msh.axis[2].stop)  # WHAT(6) - For Cartesian binning: Zmax
        # card2.setWhat(1, msh.axis[0].start)  # WHAT(1) - For Cartesian binning: Xmin
        # card2.setWhat(2, msh.axis[1].start)  # WHAT(2) - For Cartesian binning: Ymin
        # card2.setWhat(3, msh.axis[2].start)  # WHAT(3) - For Cartesian binning: Zmin
        # card2.setWhat(4, msh.axis[0].nbins)  # WHAT(4) - For Cartesian binning: number of X bins
        # card2.setWhat(5, msh.axis[1].nbins)  # WHAT(5) - For Cartesian binning: number of Y bins
        # card2.setWhat(6, msh.axis[2].nbins)  # WHAT(6) - For Cartesian binning: number of Z bins
        output_unit -= 1

        # finally add generated cards to input structure
        input_file.addCard(card1)
        card1.appendWhats(card2.whats()[1:])
