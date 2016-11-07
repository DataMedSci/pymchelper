#!/usr/bin/env python
"""
Reads PLD file in IBA format and convert to sobp.dat
which is readbale by FLUKA with source_sampler.f and SHIELD-HIT12A.

Niels Bassler 23.2.2016
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
import os
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
    def __init__(self, spotsize, energy, meterset, elsum, elements, repaints=0):
        self.spotsize = float(spotsize)
        self.energy = float(energy)
        self.meterset = float(meterset)   # MU sum of this + all previous layers
        self.elsum = float(elsum)         # sum of elements in this layer
        self.repaints = int(repaints)     # number of repaints
        self.elements = elements          # number of elements
        self.spots = int(len(elements) / 2)

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
                self.w[j] = float(token[3].strip())
                self.rf[j] = self.w[j] / dEdx(self.energy)
                j += 1


class PLDRead(object):
    """
    Class for handling PLD files.
    """
    FileIsRead = False

    def __init__(self, filename):
        """ Read the rst file."""

        if os.path.isfile(filename) is False:
            raise FileNotFoundError(filename)
        else:
            with open(filename, 'r') as fpld:
                pldlines = fpld.readlines()
            pldlen = len(pldlines)
            print("Read {} lines of data.".format(pldlen))
            i = 0
            # layer_cnt = 0
            self.layer = []

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
            self.layers = int(token[9].strip())
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

                    self.layer.append(Layer(token[1].strip(),  # Layer
                                            token[2].strip(),  # Spot1
                                            token[3].strip(),  # energy
                                            token[4].strip(),  # cumulative meter set weight including this layer
                                            # token[5].strip(),
                                            elements,  # number of elements in this layer
                                            token[6].strip()))   # number of repaints.
                i += 1


def main(args=sys.argv[1:]):
    """ Main function of the pld2sobp script.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("pld_file", help="path to .pld input file in IBA format", type=str)
    parser.add_argument("sobp_file", help="path to the SHIELD-HIT12A/FLUKA sobp.dat output file", type=str)
    parser.add_argument("-v", "--verbosity", action='count', help="increase output verbosity", default=0)
    parser.add_argument("-f", "--flip", action='store_true', help="Flip XY axis", dest="flip", default=False)
    #  parser.add_argument('-V', '--version', action='version', version=self.__version__)
    args = parser.parse_args(args)

    fn = args.pld_file

    if not os.path.isfile(fn):
        raise FileNotFoundError(fn)

    a = PLDRead(fn)
    with open(args.sobp_file, 'w') as fout:
        for i in range(a.layers):
            l = a.layer[i]
            for j in range(l.spots):

                if not args.flip:
                    fout.writelines("%-10.6f%-10.2f%-10.2f%-10.2f%-10.4e\n" % (l.energy/1000.0,
                                                                               l.x[j]/10.0,
                                                                               l.y[j]/10.0,
                                                                               (l.spotsize/10.0)*2.355,
                                                                               l.rf[j]*a.mu/a.csetweight))
                else:
                    fout.writelines("%-10.6f%-10.2f%-10.2f%-10.2f%-10.4e\n" % (l.energy/1000.0,
                                                                               l.y[j]/10.0,
                                                                               l.x[j]/10.0,
                                                                               (l.spotsize/10.0)*2.355,
                                                                               l.rf[j]*a.mu/a.csetweight))

    if args.flip:
        print("Output file was XY flipped.")

if __name__ == '__main__':
    logging.basicConfig()
    sys.exit(main(sys.argv[1:]))
