"""
Reads PLD file in IBA format and convert to sobp.dat
which is readable by FLUKA with source_sampler.f and by SHIELD-HIT12A.

TODO: Translate energy to spotsize.
"""
import sys
import logging
import argparse
from math import exp, log

logger = logging.getLogger(__name__)


def dedx_air(energy):
    """
    Calculate the mass stopping power of protons in air following ICRU 49.
    Valid from 1 to 500 MeV only.

    :params energy: Proton energy in MeV
    :returns: mass stopping power in MeV cm2/g
    """
    if energy > 500.0 or energy < 1.0:
        logger.error("Proton energy must be between 1 and 500 MeV.")
        raise ValueError("Energy = {:.2f} out of bounds.".format(energy))

    x = log(energy)
    y = 5.4041 - 0.66877 * x - 0.034441 * (x**2) - 0.0010707 * (x**3) + 0.00082584 * (x**4)
    return exp(y)


class Layer(object):
    """
    Class for handling Layers.
    """
    def __init__(self, spotsize, energy, meterset, elsum, repaints, elements):
        self.spotsize = float(spotsize)
        self.energy = float(energy)
        self.meterset = float(meterset)   # MU sum of this + all previous layers
        self.elsum = float(elsum)         # sum of elements in this layer
        self.repaints = int(repaints)     # number of repaints
        self.elements = elements          # number of elements
        self.spots = int(len(elements) / 2)  # there are two elements per spot

        self.x = [0.0] * self.spots
        self.y = [0.0] * self.spots
        self.w = [0.0] * self.spots       # MU weight
        self.rf = [0.0] * self.spots      # fluence weight

        j = 0
        for element in elements:
            token = element.split(",")
            if token[3] != "0.0":
                self.x[j] = float(token[1].strip())
                self.y[j] = float(token[2].strip())
                self.w[j] = float(token[3].strip())  # meterset weight of this spot
                self.rf[j] = self.w[j]
                j += 1  # only every second token has a element we need.


class PLDRead(object):
    """
    Class for handling PLD files.
    """

    def __init__(self, fpld):
        """ Read the rst file."""

        pldlines = fpld.readlines()
        pldlen = len(pldlines)
        logger.info("Read {} lines of data.".format(pldlen))

        self.layers = []

        # parse first line
        token = pldlines[0].split(",")
        self.beam = token[0].strip()
        self.patient_iD = token[1].strip()
        self.patient_name = token[2].strip()
        self.patient_initals = token[3].strip()
        self.patient_firstname = token[4].strip()
        self.plan_label = token[5].strip()
        self.beam_name = token[6].strip()
        self.mu = float(token[7].strip())
        self.csetweight = float(token[8].strip())
        self.nrlayers = int(token[9].strip())  # number of layers

        for i in range(1, pldlen):  # loop over all lines starting from the second one
            line = pldlines[i]
            if "Layer" in line:
                header = line

                token = header.split(",")
                # extract the subsequent lines with elements
                el_first = i + 1
                el_last = el_first + int(token[4])

                elements = pldlines[el_first:el_last]

                # read number of repaints only if 5th column is present, otherwise set to 0
                repaints_no = 0
                if 5 in token:
                    repaints_no = token[5].strip()

                self.layers.append(Layer(token[1].strip(),  # Spot1
                                         token[2].strip(),  # energy
                                         token[3].strip(),  # cumulative meter set weight including this layer
                                         token[4].strip(),  # number of elements in this layer
                                         repaints_no,  # number of repaints.
                                         elements))  # array holding all elements for this layer


def main(args=None):
    """ Main function of the pld2sobp script.
    """
    if args is None:
        args = sys.argv[1:]

    import pymchelper

    # _scaling holds the number of particles * dE/dx / MU = some constant
    # _scaling = 8.106687e7  # Calculated Nov. 2016 from Brita's 32 Gy plan. (no dE/dx)
    _scaling = 5.1821e8  # Estimated calculation Apr. 2017 from Brita's 32 Gy plan.

    parser = argparse.ArgumentParser()
    parser.add_argument('fin', metavar="input_file.pld", type=argparse.FileType('r'),
                        help="path to .pld input file in IBA format.",
                        default=sys.stdin)
    parser.add_argument('fout', nargs='?', metavar="output_file.dat", type=argparse.FileType('w'),
                        help="path to the SHIELD-HIT12A/FLUKA output file, or print to stdout if not given.",
                        default=sys.stdout)
    parser.add_argument('-f', '--flip', action='store_true', help="flip XY axis", dest="flip", default=False)
    parser.add_argument('-d', '--diag', action='store_true', help="prints additional diagnostics",
                        dest="diag", default=False)
    parser.add_argument('-s', '--scale', type=float, dest='scale',
                        help="number of particles*dE/dx per MU.", default=_scaling)
    parser.add_argument('-v', '--verbosity', action='count', help="increase output verbosity", default=0)
    parser.add_argument('-V', '--version', action='version', version=pymchelper.__version__)
    args = parser.parse_args(args)

    if args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    if args.verbosity > 1:
        logging.basicConfig(level=logging.DEBUG)

    pld_data = PLDRead(args.fin)
    args.fin.close()

    # SH12A takes any form of list of values, as long as the line is shorter than 78 Chars.
    outstr = "{:-10.6f} {:-10.2f} {:-10.2f} {:-10.2f} {:-16.6E}\n"

    meterset_weight_sum = 0.0
    particles_sum = 0.0

    for layer in pld_data.layers:
        spotsize = 2.354820045 * layer.spotsize * 0.1  # 1 sigma im mm -> 1 cm FWHM

        for spot_x, spot_y, spot_w, spot_rf in zip(layer.x, layer.y, layer.w, layer.rf):

            weight = spot_rf * pld_data.mu / pld_data.csetweight
            # Need to convert to weight by fluence, rather than weight by dose
            # for building the SOBP. Monitor Units (MU) = "meterset", are per dose
            # in the monitoring Ionization chamber, which returns some signal
            # proportional to dose to air. D = phi * S => MU = phi * S(air)
            phi_weight = weight / dedx_air(layer.energy)

            # add number of paricles in this spot
            particles_spot = args.scale * phi_weight
            particles_sum += particles_spot

            meterset_weight_sum += spot_w

            layer_xy = [spot_x * 0.1, spot_y * 0.1]

            if args.flip:
                layer_xy.reverse()

            args.fout.writelines(outstr.format(layer.energy * 0.001,  # MeV -> GeV
                                               layer_xy[0],
                                               layer_xy[1],
                                               spotsize,
                                               particles_spot))

    logger.info("Data were scaled with a factor of {:e} particles*S/MU.".format(args.scale))
    if args.flip:
        logger.info("Output file was XY flipped.")

    if args.diag:
        energy_list = [layer.energy for layer in pld_data.layers]

        # double loop over all layers and over all spots in a layer
        spot_x_list = [x for layer in pld_data.layers for x in layer.x]
        spot_y_list = [y for layer in pld_data.layers for y in layer.y]
        spot_w_list = [w for layer in pld_data.layers for w in layer.w]

        print("")
        print("Diagnostics:")
        print("------------------------------------------------")
        print("Total MUs              : {:10.4f}".format(pld_data.mu))
        print("Total meterset weigths : {:10.4f}".format(meterset_weight_sum))
        print("Total particles        : {:10.4e} (estimated)".format(particles_sum))
        print("------------------------------------------------")
        for i, energy in enumerate(energy_list):
            print("Energy in layer {:3}    : {:10.4f} MeV".format(i, energy))
        print("------------------------------------------------")
        print("Highest energy         : {:10.4f} MeV".format(max(energy_list)))
        print("Lowest energy          : {:10.4f} MeV".format(min(energy_list)))
        print("------------------------------------------------")
        print("Spot X         min/max : {:10.4f} {:10.4f} mm".format(min(spot_x_list), max(spot_x_list)))
        print("Spot Y         min/max : {:10.4f} {:10.4f} mm".format(min(spot_y_list), max(spot_y_list)))
        print("Spot meterset  min/max : {:10.4f} {:10.4f}   ".format(min(spot_w_list), max(spot_w_list)))
        print("")
    args.fout.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
