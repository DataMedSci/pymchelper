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


class BeamModel():
    """
    Beam model from a given CSV file
    """

    def __init__(self, fn, nominal=True):
        """
        Loads a beam model given as a CSV file.
        Interpolation lookup can be done as a function of nominal energy (default, nominal=True),
        or as a function of actual energy (nominal=False).
        Input columns for beam model:
            1) nominal energy [MeV]
            2) measured energy [MeV]
            3) energy spread 1 sigma [% of measured energy]
            4) primary protons per MU [1e6/MU]
            5) 1 sigma spot size x [cm]
            6) 1 sigma spot size y [cm]
            7) 1 sigma divergence x [rad]
            8) 1 sigma divergence y [rad]
            9) cov (x, x') [mm]
            10) cov (y, y') [mm]

        """
        data = np.genfromtxt(fn, delimiter=",", skip_header=1)

        # resolve by nominal energy
        if nominal:
            energy = data[:, 0]
        else:
            energy = data[:, 1]

        k = 'cubic'

        self.f_en = interp1d(energy, 	  data[:, 0],    kind=k)       # nominal energy [MeV]
        self.f_e = interp1d(energy, 	  data[:, 1],    kind=k)       # measured energy [MeV]
        # energy spread 1 sigma [% of measured energy]
        self.f_espread = interp1d(energy,      data[:, 2],    kind=k)
        self.f_ppmu = interp1d(energy, 	  data[:, 3],    kind=k)       # 1e6 protons per MU  [1e6/MU]
        self.f_sx = interp1d(energy, 	  data[:, 4],    kind=k)       # 1 sigma x [cm]
        self.f_sy = interp1d(energy, 	  data[:, 5],    kind=k)       # 1 sigma y [cm]
        self.f_divx = interp1d(energy, 	  data[:, 6],    kind=k)       # div x [rad]
        self.f_divy = interp1d(energy, 	  data[:, 7],    kind=k)       # div y [rad]
        self.f_covx = interp1d(energy, 	  data[:, 8],    kind=k)       # cov (x, x') [mm]
        self.f_covy = interp1d(energy, 	  data[:, 9],    kind=k)       # cov (y, y') [mm]
        self.data = data


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
        if spots is None:
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

    def __init__(self, bm=None):
        """ Initialize and empty plan """
        self.patient_iD = ""  # ID of patient
        self.patient_name = ""  # Last name of patient
        self.patient_initals = ""  # Initials of patient
        self.patient_firstname = ""  # Last name of patient
        self.plan_label = ""  #
        self.plan_date = ""  #
        self.nfields = 0
        self.fields = []
        self.bm = bm  # optional beam model class

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
        scaling = _scaling

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
                                          float(token[3].strip() * scaling)]  # *dEdx etc etc

                self.fields[0].layers.append(layer)
                logger.debug("appended layer %i with %i spots", len(self.fields[0].layers), layer.nspots)

    def load_DICOM_VARIAN(self, file_dcm):
        """
        """
        ds = dicom.dcmread(file_dcm.name)
        # Total number of energy layers used to produce SOBP

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

            for j, layer in enumerate(dcm_ibs):

                # gantry and couch angle is stored per energy layer, strangely
                if 'NominalBeamEnergy' in layer:
                    energy = float(layer['NominalBeamEnergy'].value)  # Nominal energy in MeV
                if 'NumberOfScanSpotPositions' in layer:
                    nspots = int(layer['NumberOfScanSpotPositions'].value)  # number of spots
                    logger.debug("Found %i spots in layer number %i at energy %f", nspots, j, energy)
                if 'NumberOfPaintings' in layer:
                    repaint = int(layer['NumberOfPaintings'].value)  # number of spots

                if 'ScanSpotPositionMap' in layer:
                    _pos = np.array(layer['ScanSpotPositionMap'].value).reshape(nspots, 2)  # spot coords in mm
                    # print(layer['ScanSpotPositionMap'].value)
                    # exit()
                    print(_pos)
                    # exit()
                if 'ScanSpotMetersetWeights' in layer:
                    _wt = np.array(layer['ScanSpotMetersetWeights'].value).reshape(nspots, 1)  # spot coords in mm
                    print(_wt)
                if 'ScanningSpotSize' in layer:
                    spotsize = np.array(layer['ScanningSpotSize'].value)

                spots = np.c_[_pos, _wt, _wt]
                # print(spots)
                # exit()
                cmu = 10.0
                enorm = energy
                emeas = energy

                field.layers.append(Layer(spotsize, enorm, emeas, cmu, repaint, nspots, spots))

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
    parser.add_argument('-b', metavar="beam_model.csv", type=argparse.FileType('r'),
                        help="optional input beam model", dest='fbm',
                        default=None)
    parser.add_argument('-f', '--flip', action='store_true',
                        help="flip XY axis", dest="flip", default=False)
    parser.add_argument('-d', '--diag', action='store_true', help="prints diagnostics",
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

    if args.fbm:
        bm = BeamModel(args.fbm.name)
    else:
        bm = None

    pln = Plan(bm)
    pln.load(args.fin)
    args.fin.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
