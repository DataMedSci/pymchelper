"""
Module for reading DICOM and PLD files

One plan may contain one or more fields.
One field may contain one or more layers.
One layer may contain one or more spots.
"""

import os
import sys
import logging
import argparse

import pydicom as dicom
import numpy as np

from math import exp, log
from scipy.interpolate import interp1d


logger = logging.getLogger(__name__)

s2fwhm = 2.0 * np.sqrt(2.0 * np.log(2.0))  # 1 FWHM = 2.355 * sigma


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
    A single energy layer in a plan
    """

    def __init__(self, spotsize=np.array([1.0, 1.0]),
                 enorm=100.0, emeas=100.0, cmu=10000.0, repaint=0, nspots=1, spots=None):
        """
        Initialize and empty plan

        spotsize: FWHM swidth of spot in cm along x and y axis, respectively
        enorm : nominal energy in MeV
        emeas : measured energy in MeV at exit nozzle
        cmu : cummulative monitor units for this layers
        repaint: number of repainting, 0 for no repaints TODO: check what is convention here.
        spots : np.array([[x_i, y_i, mu_i, n], [...], ...) for i spots.
                x,y are isocenter plane positions in cm.
                mu is monitor units or meterset weights for the individual spots
                n is the estimated number of primary particles for this spot
        """
        self.spotsize = spotsize      # spot size in FWHM cm
        self.energy_nominal = enorm   # nominal energy in MeV
        self.energy_measured = emeas  # measured energy in MeV
        self.cmu = cmu                # cummulative monitor units for this layer
        self.repaint = repaint        # TODO: check me
        self.nspots = nspots          # number of spots found in this layer
        if not spots:
            self.spots = np.zeros((nspots, 4))
        else:
            self.spots = spots            # list of spot positions in cm, as [[x, y, mu, n], ...]


class Field(object):
    """
    A single field
    """

    def __init__(self):
        self.nlayers = 0   # number of layers found
        self.layers = []
        self.dose = 0.0
        self.cmu = 0.0  # cummulative meterset or monitor units for entire field
        self.csetweight = 0.0  # IBA specific
        self.gantry = 0
        self.couch = 0


class Plan(object):
    """
    Class for handling PLD files.
    """

    def __init__(self):
        """ Initialize and empty plan """
        self.patient_iD = ""  # ID of patient
        self.patient_name = ""  # Last name of patient
        self.patient_initals = ""  # Initials of patient
        self.patient_firstname = ""  # Last name of patient
        self.plan_label = ""  #
        self.plan_date = ""  #
        self.nfields = 0
        self.fields = []

    def load(self, file):
        """
        Load file, autodiscovery by suffix.
        """
        print("jjj")
        ext = os.path.splitext(file.name)[-1].lower()
        if ext == ".pld":
            self.load_PLD_IBA(file)
        if ext == ".dcm":
            self.load_DICOM_VARIAN(file)
        if ext == ".rst":
            self.load_RASTER_GSI(file)

    def load_PLD_IBA(self, file_pld):
        """
        file_pld : a file pointer to a .pld file, opened for reading

        Here we assume there is only a single field in every .pld file
        """

        # _scaling holds the number of particles * dE/dx / MU = some constant
        # _scaling = 8.106687e7  # Calculated Nov. 2016 from Brita's 32 Gy plan. (no dE/dx)
        _scaling = 5.1821e8  # Estimated calculation Apr. 2017 from Brita's 32 Gy plan.

        field = Field()
        self.fields.append(field)
        self.nfields = 1

        pldlines = file_pld.readlines()
        pldlen = len(pldlines)
        logger.info("Read {} lines of data.".format(pldlen))

        field.layers = []
        field.nlayers = 0

        # First line in PLD file contains both plan and field data
        tokens = pldlines[0].split(",")
        # _ = tokens[0].strip()
        self.patient_iD = tokens[1].strip()
        self.patient_name = tokens[2].strip()
        self.patient_initals = tokens[3].strip()
        self.patient_firstname = tokens[4].strip()
        self.plan_label = tokens[5].strip()
        self.beam_name = tokens[6].strip()
        field.cmu = float(tokens[7].strip())
        field.csetweight = float(tokens[8].strip())
        field.nlayers = int(tokens[9].strip())  # number of layers

        for i in range(1, pldlen):  # loop over all lines starting from the second one
            line = pldlines[i]
            if "Layer" in line:  # each new layers starts with the "Layer" keyword
                # the "Layer" header is formated as
                # "Layer, "
                header = line
                tokens = header.split(",")
                # extract the subsequent lines with elements
                el_first = i + 1
                el_last = el_first + int(tokens[4])

                elements = pldlines[el_first:el_last]  # each line starting with "Element" string is a spot.

                # tokens[0] just holds the "Layer" keyword
                spotsize = float(tokens[1].strip()) * s2fwhm * 0.1  # convert mm sigma to cm FWHM
                energy_nominal = float(tokens[2].strip())
                cmu = float(tokens[3].strip())
                nspots = int(tokens[4].strip())

                # read number of repaints only if 5th column is present, otherwise set to 0
                nrepaint = 0  # TODO: suspect repaints = 1 means all dose will be delivered once.
                if len(tokens) > 5:
                    nrepaint = tokens[5].strip()

                layer = Layer([spotsize, spotsize], energy_nominal, energy_nominal, cmu, nrepaint, nspots)

                print(dir(layer))
                print(layer.spots)
                # exit()

                for j, element in enumerate(elements):
                    token = element.split(",")
                    # the .pld file has every spot position repeated, but MUs are only in
                    # every second line, for reasons unknown.
                    if token[3] != "0.0":
                        layer.spots[j] = [float(token[1].strip()),
                                          float(token[2].strip()),
                                          float(token[3].strip()),
                                          0.0]

                self.fields[0].layers.append(layer)
                logger.debug("appended layer %i with %i spots", len(self.fields[0].layers), layer.nspots)

    def load_DICOM_VARIAN(self, file_dcm):
        """
        """
        ds = dicom.dcmread(file_dcm.name)
        # Total number of energy layers used to produce SOBP
        print("jere")

        self.patient_iD = ds['PatientID'].value
        self.patient_name = ds['PatientName'].value
        self.patient_initals = ""
        self.patient_firstname = ""
        self.plan_label = ds['RTPlanLabel'].value
        self.plan_date = ds['RTPlanDate'].value
        self.beam_name = ""

        self.nfields = int(ds['FractionGroupSequence'][0]['NumberOfBeams'].value)
        logger.debug("Found %i fields", self.nfields)

        dcm_fgs = ds['FractionGroupSequence'][0]['ReferencedBeamSequence']  # fields for given group number
        print(dcm_fgs)

        for i, dcm_field in enumerate(dcm_fgs):
            field = Field()
            self.fields.append(field)
            field.dose = float(dcm_field['BeamDose'].value)
            field.cmu = float(dcm_field['BeamMeterset'].value)
            field.csetweight = 1.0
            field.nlayers = int(ds['IonBeamSequence'][i]['NumberOfControlPoints'].value)
            dcm_ibs = ds['IonBeamSequence'][i]['IonControlPointSequence']  # layers for given field number
            logger.debug("Found %i layers in field number %i", field.nlayers, i)

            # for i, layer in enumerate(layers):
            # energy = float(layer['IonControlPointSequence'][0]['NominalBeamEnergy'].value)  # Nomnial energy in MeV
            # npos = int(layer['IonControlPointSequence'][0]['NumberOfScanSpotPositions'].value)  # number of spots
            # _pflat = np.array(layer['IonControlPointSequence'][0]['ScanSpotPositionMap'].value)  # spot coords in mm

        def load_RASTER_GSI(self, file_rst):
            """
            """
            pass

        def inspect(self):
            """
            """
            pass


def main(args=None):
    """ Main function of the pld2sobp script.
    """
    if args is None:
        args = sys.argv[1:]

    import pymchelper

    parser = argparse.ArgumentParser()
    parser.add_argument('fin', metavar="input_file.pld", type=argparse.FileType('r'),
                        help="path to .pld input file in IBA format.",
                        default=sys.stdin)
    parser.add_argument('fout', nargs='?', metavar="output_file.dat", type=argparse.FileType('w'),
                        help="path to the SHIELD-HIT12A/FLUKA output file, or print to stdout if not given.",
                        default=sys.stdout)
    parser.add_argument('-f', '--flip', action='store_true',
                        help="flip XY axis", dest="flip", default=False)
    parser.add_argument('-d', '--diag', action='store_true', help="prints additional diagnostics",
                        dest="diag", default=False)
    parser.add_argument('-s', '--scale', type=float, dest='scale',
                        help="number of particles*dE/dx per MU.", default=-1.0)
    parser.add_argument('-v', '--verbosity', action='count',
                        help="increase output verbosity", default=0)
    parser.add_argument('-V', '--version', action='version', version=pymchelper.__version__)
    args = parser.parse_args(args)

    if args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)

    if args.verbosity > 1:
        logging.basicConfig(level=logging.DEBUG)

    pln = Plan()
    pln.load(args.fin)
    args.fin.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
