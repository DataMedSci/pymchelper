"""
Module for reading DICOM and PLD files.

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

from dataclasses import dataclass, field
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
    """Beam model from a given CSV file."""

    def __init__(self, fn, nominal=True):
        """
        Load a beam model given as a CSV file.

        Interpolation lookup can be done as a function of nominal energy (default, nominal=True),
        or as a function of actual energy (nominal=False).

        Header rows will be discarded and must be prefixed with '#'.

        Input columns for beam model:
            1) nominal energy [MeV]
            2) measured energy [MeV]
            3) energy spread 1 sigma [% of measured energy]
            4) primary protons per MU [1e6/MU]
            5) 1 sigma spot size x [cm]
            6) 1 sigma spot size y [cm]
        Optionally, 4 more columns may be given:
            7) 1 sigma divergence x [rad]
            8) 1 sigma divergence y [rad]
            9) cov (x, x') [mm]
            10) cov (y, y') [mm]

        TODO: get rid of scipy dependency
        """
        data = np.genfromtxt(fn, delimiter=",", invalid_raise=False, comments='#')

        # resolve by nominal energy
        if nominal:
            energy = data[:, 0]
        else:
            energy = data[:, 1]

        k = 'cubic'

        cols = len(data[0])
        logger.debug("Number of columns in beam model: %i", cols)

        self.has_divergence = False

        if cols == 6 or cols == 10:
            self.f_en = interp1d(energy, data[:, 0], kind=k)       # nominal energy [MeV]
            self.f_e = interp1d(energy, data[:, 1], kind=k)        # measured energy [MeV]
            self.f_espread = interp1d(energy, data[:, 2], kind=k)  # energy spread 1 sigma [% of measured energy]
            self.f_ppmu = interp1d(energy, data[:, 3], kind=k)     # 1e6 protons per MU  [1e6/MU]
            self.f_sx = interp1d(energy, data[:, 4], kind=k)       # 1 sigma x [cm]
            self.f_sy = interp1d(energy, data[:, 5], kind=k)       # 1 sigma y [cm]
        else:
            logger.error("invalid column count")

        if cols == 10:
            logger.debug("Beam model has divergence data")
            self.has_divergence = True
            self.f_divx = interp1d(energy, data[:, 6], kind=k)     # div x [rad]
            self.f_divy = interp1d(energy, data[:, 7], kind=k)     # div y [rad]
            self.f_covx = interp1d(energy, data[:, 8], kind=k)     # cov (x, x') [mm]
            self.f_covy = interp1d(energy, data[:, 9], kind=k)     # cov (y, y') [mm]

        self.data = data


@dataclass
class Spot:
    # TODO: not sure this is needed at all
    """TODO."""

    x: float = 0.0
    y: float = 0.0
    mu: float = 0.0  # meterset weight (this is proportional to the dose in the air filled monitor IC)
    wt: float = 0.0  # actual number of particles, if possible, absolute


@dataclass
class Layer:
    """
    Handle layers in a plan.

    spots : np.array([[x_i, y_i, mu_i, n], [...], ...) for i spots.
            x,y are isocenter plane positions in cm.
            mu is monitor units or meterset weights for the individual spots
            n is the estimated number of primary particles for this spot
    spotsize: FWHM swidth of spot in cm along x and y axis, respectively
    enorm : nominal energy in MeV
    emeas : measured energy in MeV at exit nozzle
    cmu : cummulative monitor units for this layers
    repaint : number of repainting, 0 for no repaints TODO: check what is convention here.
    nspots : number of spots in total
    """

    spots: np.array
    spotsize: np.ndarray([2, 1])
    energy_nominal: float = 100.0
    energy_measured: float = 100.0
    cmu: float = 10000.0
    repaint: int = 0
    nspots: int = 1
    # spots: List[Spot]  # not sure if this will be needed


@dataclass
class Field:
    """
    A single field.

    # TODO: gantry/field may be on layer level
    """

    layers: list = field(default_factory=list)  # https://stackoverflow.com/questions/53632152/
    nlayers: int = 0  # number of layers in this field
    dose: float = 0.0  # dose in [Gy]
    cmu: float = 0.0  # cummulative MU of all layers in this field
    _pld_csetweight: float = 0.0  # IBA specific
    gantry: float = 0.0
    couch: float = 0.0
    scaling: float = 1.0  # scaling applied to all particle numbers


@dataclass
class Plan:
    """
    Class for handling treatment plans.

    One plan may consist of one or more fields.
    One field may conatain one of more layers.

    Beam model is optional, but needed for exact modeling of the beam.
    If no beam model is given, MUs are translated to particle numbers using approximate stopping power for air (dEdx).
    """

    fields: list = field(default_factory=list)  # https://stackoverflow.com/questions/53632152/
    patient_iD: str = ""  # ID of patient
    patient_name: str = ""  # Last name of patient
    patient_initals: str = ""  # Initials of patient
    patient_firstname: str = ""  # Last name of patient
    plan_label: str = ""  #
    plan_date: str = ""  #
    nfields: int = 0
    bm: BeamModel = None  # optional beam model class
    flip_xy: bool = False  # flag whether x and y has been flipped


def load_beammodel(fn):
    """Returns a beam model object"""
    bm = BeamModel(fn)
    return bm


def load(file, beam_model=None, scaling=1.0, flip_xy=False):
    """Load file, autodiscovery by suffix."""
    logger.debug("load() autodiscovery")
    ext = os.path.splitext(file.name)[-1].lower()  # extract suffix, incl. dot separator

    if ext == ".pld":
        p = load_PLD_IBA(file, beam_model, scaling, flip_xy)
    if ext == ".dcm":
        p = load_DICOM_VARIAN(file, beam_model, scaling, flip_xy)  # so far I have no other dicom files
    if ext == ".rst":
        p = load_RASTER_GSI(file, beam_model, scaling, flip_xy)
    return p


def load_PLD_IBA(file_pld, beam_model=None, scaling=1.0, flip_xy=False):
    """
    file_pld : a file pointer to a .pld file, opened for reading.

    Here we assume there is only a single field in every .pld file.
    """
    # _scaling holds the number of particles * dE/dx / MU = some constant
    # _scaling = 8.106687e7  # Calculated Nov. 2016 from Brita's 32 Gy plan. (no dE/dx)
    ppmu = 5.1821e8  # protons per MU, Estimated calculation Apr. 2017 from Brita's 32 Gy plan.

    p = Plan()
    p.bm = beam_model

    myfield = Field()  # avoid collision with dataclasses.field
    p.fields = [myfield]
    p.nfields = 1

    pldlines = file_pld.readlines()
    pldlen = len(pldlines)
    logger.info("Read {} lines of data.".format(pldlen))

    field.layers = []
    field.nlayers = 0

    # First line in PLD file contains both plan and field data
    tokens = pldlines[0].split(",")
    # _ = tokens[0].strip()
    p.patient_iD = tokens[1].strip()
    p.patient_name = tokens[2].strip()
    p.patient_initals = tokens[3].strip()
    p.patient_firstname = tokens[4].strip()
    p.plan_label = tokens[5].strip()
    p.beam_name = tokens[6].strip()
    field.cmu = float(tokens[7].strip())   # total amount of MUs in this field
    field._pld_csetweight = float(tokens[8].strip())
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
            logger.debug(tokens)

            # read number of repaints only if 5th column is present, otherwise set to 0
            nrepaint = 0  # TODO: suspect repaints = 1 means all dose will be delivered once.
            if len(tokens) > 5:
                nrepaint = tokens[5].strip()

            spots = np.array([])

            layer = Layer(spots, [spotsize, spotsize], energy_nominal, energy_nominal, cmu, nrepaint, nspots)

            particles_sum = 0
            for j, element in enumerate(elements):  # loop over each spot in this layer
                token = element.split(",")
                # the .pld file has every spot position repeated, but MUs are only in
                # every second line, for reasons unknown.
                _x = float(token[0].strip())
                _y = float(token[1].strip())
                _wt = float(token[2].strip())
                if _wt != "0.0":
                    _mu = float(token[3].strip())
                    weight = ppmu * _mu * field.cmu / field._pld_csetweight
                    # Need to convert to weight by fluence, rather than weight by dose
                    # for building the SOBP. Monitor Units (MU) = "meterset", are per dose
                    # in the monitoring Ionization chamber, which returns some signal
                    # proportional to dose to air. D = phi * S => MU = phi * S(air)
                    phi_weight = weight / dedx_air(layer.energy)

                    # add number of paricles in this spot
                    particles_spot = scaling * phi_weight
                    particles_sum += particles_spot

                np.append([_x, _y, _wt, particles_spot], layer.spots)

            p.fields[0].layers.append(layer)
            logger.debug("appended layer %i with %i spots", len(p.fields[0].layers), layer.nspots)
    return p


def load_DICOM_VARIAN(file_dcm, beam_model=None, scaling=1.0, flip_xy=False):
    """Load varian type dicom plans."""
    ds = dicom.dcmread(file_dcm.name)
    # Total number of energy layers used to produce SOBP

    p = Plan()
    p.patient_iD = ds['PatientID'].value
    p.patient_name = ds['PatientName'].value
    p.patient_initals = ""
    p.patient_firstname = ""
    p.plan_label = ds['RTPlanLabel'].value
    p.plan_date = ds['RTPlanDate'].value
    p.beam_name = ""

    p.nfields = int(ds['FractionGroupSequence'][0]['NumberOfBeams'].value)
    logger.debug("Found %i fields", p.nfields)

    dcm_fgs = ds['FractionGroupSequence'][0]['ReferencedBeamSequence']  # fields for given group number
    print(dcm_fgs)

    for i, dcm_field in enumerate(dcm_fgs):
        myfield = Field()
        p.fields.append(myfield)
        myfield.dose = float(dcm_field['BeamDose'].value)
        myfield.cmu = float(dcm_field['BeamMeterset'].value)
        myfield.csetweight = 1.0
        myfield.nlayers = int(ds['IonBeamSequence'][i]['NumberOfControlPoints'].value)
        dcm_ibs = ds['IonBeamSequence'][i]['IonControlPointSequence']  # layers for given field number
        logger.debug("Found %i layers in field number %i", myfield.nlayers, i)

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
            if 'ScanSpotMetersetWeights' in layer:
                _wt = np.array(layer['ScanSpotMetersetWeights'].value).reshape(nspots, 1)  # spot coords in mm
            if 'ScanningSpotSize' in layer:
                spotsize = np.array(layer['ScanningSpotSize'].value)

            spots = np.c_[_pos, _wt, _wt]
            cmu = 10.0
            enorm = energy
            emeas = energy

            myfield.layers.append(Layer(spotsize, enorm, emeas, cmu, repaint, nspots, spots))
    return p


def load_RASTER_GSI(file_rst, beam_model=None, scaling=1.0, flip_xy=False):
    """TODO: this is implemented in pytrip. Import it?."""
    p = Plan()
    return p


def main(args=None):
    """TODO: move this to makesobp script."""
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
                        help="number of particles*dE/dx per MU.", default=1.0)
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

    pln = load(args.fin, bm, args.scale, args.flip)
    args.fin.close()
    print(pln)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
