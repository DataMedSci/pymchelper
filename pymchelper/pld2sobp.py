#!/usr/bin/env python
"""
Reads PLD file in IBA format and convert to sobp.dat
which is readbale by FLUKA with source_sampler.f and SHIELD-HIT12A.

<niels.bassler@fysik.su.se>

TODO: Translate energy to spotsize.
E[MeV]    sigmaY_GCS [mm]    sigmaX_GCS [mm]
70    6,476    6,358
80    5,944    5,991
90    5,437    5,352
100    5,081    5,044
110    4,820    4,828
120    4,677    4,677
130    4,401    4,431
140    4,207    4,104
150    3,977    3,956
160    3,758    3,687
170    3,609    3,477
180    3,352    3,288
190    3,131    3,034
200    2,886    2,803
210    2,713    2,645
220    2,529    2,461
225    2,522    2,452

"""
import sys
import logging
import argparse

logger = logging.getLogger(__name__)


def dEdx(energy):
    """
    PSTAR stopping power for protons in the interval 10 - 250 MeV
    Energy is in [MeV]
    Stopping power is in [MeV cm2/g]
    """

    if (energy > 250.0) or (energy < 10.0):
        logger.error("dEdx error: {} MeV is out of bounds.".format(energy))
        raise IOError()

    a0 = 265.78
    a1 = -0.828879
    a2 = 0.647173

    return a0 * pow(energy, a1) + a2


class Layer(object):
    """ Class for handling Layers.
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

        for i in range(len(elements)):
            token = elements[i].split(",")
            if token[3] != "0.0":
                self.x[j] = float(token[1].strip())
                self.y[j] = float(token[2].strip())
                self.w[j] = float(token[3].strip())  # meterset weight of this spot
                self.rf[j] = self.w[j] / dEdx(self.energy)  # relative particle number
                j += 1


class PLDRead(object):
    """
    Class for handling PLD files.
    """

    def __init__(self, fpld):
        """ Read the rst file."""

        pldlines = fpld.readlines()
        pldlen = len(pldlines)
        logger.info("Read {} lines of data.".format(pldlen))
        i = 0

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
        i += 1

        while i < pldlen:
            line = pldlines[i]
            if "Layer" in line:
                header = line
                token = header.split(",")
                # extract the subsequent lines with elements
                el_first = i + 1
                el_last = el_first + int(token[4])

                elements = pldlines[el_first:el_last]

                self.layers.append(Layer(token[1].strip(),  # Spot1
                                        token[2].strip(),  # energy
                                        token[3].strip(),  # cumulative meter set weight including this layer
                                        token[4].strip(),  # number of elements in this layer
                                        token[5].strip(),  # number of repaints.
                                        elements))  # array holding all elements for this layer
            i += 1


def main(args=sys.argv[1:]):
    """ Main function of the pld2sobp script.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('fin', metavar="input_file.pld", type=argparse.FileType('r'),
                        help="path to .pld input file in IBA format.",
                        default=sys.stdin)
    parser.add_argument('fout', nargs='?', metavar="output_file.dat", type=argparse.FileType('w'),
                        help="path to the SHIELD-HIT12A/FLUKA output file, or print to stdout if not given.",
                        default=sys.stdout)
    parser.add_argument("-v", "--verbosity", action='count', help="increase output verbosity", default=0)
    parser.add_argument("-f", "--flip", action='store_true', help="flip XY axis", dest="flip", default=False)
    parser.add_argument("-d", "--diag", action='store_true', help="prints additional diagnostics",
                        dest="diag", default=False)
    parser.add_argument("-s", "--scale", type=float, dest='scale',
                        help="number of particles per MU.", default=1.0)
    #  parser.add_argument('-V', '--version', action='version', version=self.__version__)
    args = parser.parse_args(args)

    if args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    if args.verbosity > 1:
        logging.basicConfig(level=logging.DEBUG)

    a = PLDRead(args.fin)
    args.fin.close()

    msw_sum = 0.0
    
    for l in a.layers:
        for j in range(l.spots):

            spotsize = 2.354820045 * l.spotsize * 0.1  # 1 sigma im mm -> 1 cm FWHM
            weight = l.rf[j] * a.mu / a.csetweight * args.scale
            msw_sum += l.w[j]

            # SH12A takes any form of list of values, as long as the line is shorter than 78 Chars.
            outstr = "{:-10.6f} {:-10.2f} {:-10.2f} {:-10.2f} {:-16.6E}\n"

            if args.flip:
                args.fout.writelines(outstr.format(l.energy * 0.001,  # MeV -> GeV
                                                   l.y[j] * 0.1,      # -> cm
                                                   l.x[j] * 0.1,
                                                   spotsize,
                                                   weight))
            else:
                args.fout.writelines(outstr.format(l.energy * 0.001,  # MeV -> GeV
                                                   l.x[j] * 0.1,      # -> cm
                                                   l.y[j] * 0.1,
                                                   spotsize,
                                                   weight))

    logger.info("Data were scaled with a factor of {:e} particles/MU.".format(args.scale))
    if args.flip:
        logger.info("Output file was XY flipped.")


    if args.diag:
        energy_list = [0.0]*len(a.layers)
        spotx_list = [0.0, 0.0]  # placeholder for min max values
        spoty_list = [0.0, 0.0]  # placeholder for min max values
        spotw_list = [0.0, 0.0]  # placeholder for min max values


        
        for i,ll in enumerate(a.layers):
            energy_list[i] = ll.energy

            if spotx_list[0] > min(ll.x):
                spotx_list[0] = min(ll.x)
            if spotx_list[1] < max(ll.x):
                spotx_list[1] = max(ll.x)

            if spoty_list[0] > min(ll.y):
                spoty_list[0] = min(ll.y)
            if spoty_list[1] < max(ll.y):
                spoty_list[1] = max(ll.y)

            if spotw_list[0] > min(ll.w):
                spotw_list[0] = min(ll.w)
            if spotw_list[1] < max(ll.w):
                spotw_list[1] = max(ll.w)

        print("")
        print("Diagnostics:")
        print("------------------------------------------------")
        print("Total MUs              : {:10.4f}".format(a.mu))
        print("Total meterset weigths : {:10.4f}".format(msw_sum))
        print("------------------------------------------------")
        for i,energy in enumerate(energy_list):
            print("Energy in layer {:3}    : {:10.4f} MeV".format(i,energy))
        print("------------------------------------------------")
        print("Highest energy         : {:10.4f} MeV".format(max(energy_list)))
        print("Lowest energy          : {:10.4f} MeV".format(min(energy_list)))
        print("------------------------------------------------")
        print("Spot X         min/max : {:10.4f} {:10.4f} mm".format(min(spotx_list),max(spotx_list)))
        print("Spot Y         min/max : {:10.4f} {:10.4f} mm".format(min(spoty_list),max(spoty_list)))
        print("Spot meterset  min/max : {:10.4f} {:10.4f}   ".format(min(spotw_list),max(spotw_list)))
        print("")
    args.fout.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
