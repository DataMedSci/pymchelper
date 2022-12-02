"""
Module for reading DICOM and PLD files.

One plan may contain one or more fields.
One field may contain one or more layers.
One layer may contain one or more spots.
"""

import sys
import logging
import argparse
import pymchelper

import pydicom as dicom
import numpy as np
from pathlib import Path
from typing import Optional

from dataclasses import dataclass, field
from math import exp, log
from scipy.interpolate import interp1d

logger = logging.getLogger(__name__)

s2fwhm = 2.0 * np.sqrt(2.0 * np.log(2.0))  # 1 FWHM = 2.355 * sigma


def dedx_air(energy: float) -> float:
    """
    Calculate the mass stopping power of protons in air following ICRU 49.

    Valid from 1 to 500 MeV only.

    :params energy: Proton energy in MeV
    :returns: mass stopping power in MeV cm2/g
    """
    if energy > 500.0 or energy < 1.0:
        logger.error("Proton energy must be between 1 and 500 MeV.")
        raise ValueError(f"Energy = {energy:.2f} out of bounds.")
    x = log(energy)
    y = 5.4041 - 0.66877 * x - 0.034441 * (x**2) - 0.0010707 * (x**3) + 0.00082584 * (x**4)
    return exp(y)


class BeamModel():
    """Beam model from a given CSV file."""

    def __init__(self, fn: Path, nominal=True):
        """
        Load a beam model given as a CSV file.

        Interpolation lookup can be done as a function of nominal energy (default, nominal=True),
        or as a function of actual energy (nominal=False).

        Header rows will be discarded and must be prefixed with '#'.

        Input columns for beam model:
            1) nominal energy [MeV]
            2) measured energy [MeV]
            3) energy spread 1 sigma [MeV]
            4) primary protons per MU [protons/MU]
            5) 1 sigma spot size x [mm]
            6) 1 sigma spot size y [mm]
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

        if cols in (6, 10):
            self.f_en = interp1d(energy, data[:, 0], kind=k)  # nominal energy [MeV]
            self.f_e = interp1d(energy, data[:, 1], kind=k)  # measured energy [MeV]
            self.f_espread = interp1d(energy, data[:, 2], kind=k)  # energy spread 1 sigma [% of measured energy]
            self.f_ppmu = interp1d(energy, data[:, 3], kind=k)  # 1e6 protons per MU  [1e6/MU]
            self.f_sx = interp1d(energy, data[:, 4], kind=k)  # 1 sigma x [cm]
            self.f_sy = interp1d(energy, data[:, 5], kind=k)  # 1 sigma y [cm]
        else:
            logger.error("invalid column count")

        if cols == 10:
            logger.debug("Beam model has divergence data")
            self.has_divergence = True
            self.f_divx = interp1d(energy, data[:, 6], kind=k)  # div x [rad]
            self.f_divy = interp1d(energy, data[:, 7], kind=k)  # div y [rad]
            self.f_covx = interp1d(energy, data[:, 8], kind=k)  # cov (x, x') [mm]
            self.f_covy = interp1d(energy, data[:, 9], kind=k)  # cov (y, y') [mm]

        self.data = data


@dataclass
class Layer:
    """
    Handle layers in a plan.

    spots : np.array([[x_i, y_i, mu_i, n], [...], ...) for i spots.
            x,y : are spot positions at isocenter in [mm].
            mu  : are monitor units or meterset weights for the individual spots [MU]
            n   : is the estimated number of primary particles for this spot
    spotsize: np.array() FWHM width of spot in along x and y axis, respectively [mm]
    enorm : nominal energy in [MeV]
    emeas : measured energy in [MeV] at exit nozzle
    cum_mu : cumulative monitor units for this layers [MU]
    repaint : number of repainting, 0 for no repaints TODO: check what is convention here.
    n_spots : number of spots in total
    mu_to_part_coef : conversion coefficient from MU to number of particles (depends on energy)
    """

    spots: np.array = field(default_factory=np.array)
    spotsize: np.array = field(default_factory=np.array)
    energy_nominal: float = 100.0
    energy_measured: float = 100.0
    espread: float = 0.0
    cum_mu: float = 0.0
    cum_particles: float = 0.0  # cumulative number of particles
    xmin: float = 0.0
    xmax: float = 0.0
    ymin: float = 0.0
    ymax: float = 0.0
    repaint: int = 0
    n_spots: int = 1
    mu_to_part_coef: float = 1.0
    is_empty: bool = True  # marker if there are no MUs in this layer


@dataclass
class Field:
    """A single field."""

    layers: list = field(default_factory=list)  # https://stackoverflow.com/questions/53632152/
    n_layers: int = 0  # number of layers in this field
    dose: float = 0.0  # dose in [Gy]
    cum_mu: float = 0.0  # cumulative MU of all layers in this field
    cum_particles: float = 0.0  # cumulative number of particles
    pld_csetweight: float = 0.0  # IBA specific
    # gantry: float = 0.0
    # couch: float = 0.0
    scaling: float = 1.0  # scaling applied to all particle numbers
    xmin: float = 0.0
    xmax: float = 0.0
    ymin: float = 0.0
    ymax: float = 0.0

    def diagnose(self):
        """Print overview of field."""
        energy_list = [layer.energy_nominal for layer in self.layers]
        emin = min(energy_list)
        emax = max(energy_list)

        indent = "   "  # indent layer output, since this is a branch

        print(indent + "------------------------------------------------")
        print(indent + f"Energy layers          : {self.n_layers:10d}")
        print(indent + f"Total MUs              : {self.cum_mu:10.4f}")
        print(indent + f"Total particles        : {self.cum_particles:10.4e} (estimated)")
        print(indent + "------------------------------------------------")
        for i, layer in enumerate(self.layers):
            print(indent + f"   Layer {i: 3}: {layer.energy_nominal: 10.4f} MeV " + f"   {layer.n_spots:10d} spots")
        print(indent + "------------------------------------------------")
        print(indent + f"Highest energy         : {emin:10.4f} MeV")
        print(indent + f"Lowest energy          : {emax:10.4f} MeV")
        print(indent + "------------------------------------------------")
        print(indent + f"Spot field min/max X   : {self.xmin:+10.4f} {self.xmax:+10.4f} mm")
        print(indent + f"Spot field min/max Y   : {self.ymin:+10.4f} {self.ymax:+10.4f} mm")
        print(indent + "------------------------------------------------")
        print("")


@dataclass
class Plan:
    """
    Class for handling treatment plans.

    One plan may consist of one or more fields.
    One field may contain one of more layers.

    Beam model is optional, but needed for exact modeling of the beam.
    If no beam model is given, MUs are translated to particle numbers using approximate stopping power for air (dEdx)
    and empirical scaling factors.
    """

    fields: list = field(default_factory=list)  # https://stackoverflow.com/questions/53632152/
    patient_id: str = ""  # ID of patient
    patient_name: str = ""  # Last name of patient
    patient_initals: str = ""  # Initials of patient
    patient_firstname: str = ""  # Last name of patient
    plan_label: str = ""  #
    plan_date: str = ""  #
    n_fields: int = 0
    beam_model: Optional[BeamModel] = None  # optional beam model class
    beam_name: str = ""
    flip_xy: bool = False  # flag whether x and y has been flipped

    # factor holds the number of particles * dE/dx / MU = some constant
    # MU definitions is arbitrary and my vary from vendor to vendor.
    # This will only be used if no beam model is available, and is based on estimates.
    factor: float = 1.0  # vendor specific factor needed for translating MUs to number of particles
    scaling: float = 1.0

    def apply_beammodel(self):
        """Adjust plan to beam model."""
        if self.beam_model:
            for myfield in self.fields:
                for layer in myfield.layers:
                    # calculate number of particles
                    layer.mu_to_part_coef = self.beam_model.f_ppmu(layer.energy_nominal)
                    layer.energy_measured = self.beam_model.f_e(layer.energy_nominal)
                    layer.espread = self.beam_model.f_espread(layer.energy_nominal)
                    layer.spots[:, 3] = layer.spots[:, 2] * layer.mu_to_part_coef * myfield.scaling
                    layer.spotsize = np.array(
                        [self.beam_model.f_sx(layer.energy_nominal),
                         self.beam_model.f_sy(layer.energy_nominal)]) * s2fwhm
        else:
            for myfield in self.fields:
                for layer in myfield.layers:
                    # if there is no beam model available, we will simply use air stopping power
                    # since MU is proportional to dose in monitor chamber, which means fluence ~ D_air / dEdx(air)
                    layer.mu_to_part_coef = self.factor / dedx_air(layer.energy_measured)
                    layer.spots[:, 3] = layer.spots[:, 2] * layer.mu_to_part_coef * myfield.scaling
                    # old IBA code something like:
                    # weight = mu_to_part_coef * _mu2 * field.cmu / field.pld_csetweight
                    # phi_weight = weight / dedx_air(layer.energy_measured)

        # set cumulative sums
        for myfield in self.fields:
            myfield.cum_particles = 0.0
            myfield.cum_mu = 0.0
            myfield.xmin = 0.0
            myfield.xmax = 0.0
            myfield.ymin = 0.0
            myfield.ymax = 0.0

            # set layer specific values
            for layer in myfield.layers:
                layer.n_spots = len(layer.spots)
                layer.xmin = layer.spots[:, 0].min()
                layer.xmax = layer.spots[:, 0].max()
                layer.ymin = layer.spots[:, 1].min()
                layer.ymax = layer.spots[:, 1].max()
                layer.cum_mu = layer.spots[:, 2].sum()
                if layer.cum_mu > 0.0:
                    layer.is_empty = False
                layer.cum_particles = layer.spots[:, 3].sum()

                myfield.cum_particles += layer.cum_particles
                myfield.cum_mu += layer.cum_mu

                if layer.xmin < myfield.xmin:
                    myfield.xmin = layer.xmin
                if layer.xmax > myfield.xmax:
                    myfield.xmax = layer.xmax

                if layer.ymin < myfield.ymin:
                    myfield.ymin = layer.ymin
                if layer.ymax > myfield.ymax:
                    myfield.ymax = layer.ymax

    def diagnose(self):
        """Print overview of plan."""
        print("Diagnostics:")
        print("---------------------------------------------------")
        print(f"Patient Name           : '{self.patient_name}'       [{self.patient_initals}]")
        print(f"Patient ID             : {self.patient_id}")
        print(f"Plan label             : {self.plan_label}")
        print(f"Plan date              : {self.plan_date}")
        print(f"Number of Fields       : {self.n_fields:2d}")

        for i, myfield in enumerate(self.fields):
            print("---------------------------------------------------")
            print(f"   Field                  : {i + 1:02d}/{self.n_fields:02d}:")
            myfield.diagnose()
            print("")

    def export(self, fn: Path, cols: int, field_nr: int):
        """
        Export file to sobp.dat format, 'cols' marking the number of columns.

        fn : filename
        cols : number of columns for output format.
               5 column format: energy[GeV] x[cm] y[cm] FWHM[cm] weight
               6 column format: energy[GeV] x[cm] y[cm] FWHMx[cm] FWHMy[cm] weight
               7 column format: energy[GeV] sigmaT0[GeV] x[cm] y[cm] FWHM[cm] weight
        field_nr: in case of multiple field, select what field to export, use '0' to export all fields.

        TODO:
               11 columns: ENERGY, ESPREAD, X, Y, FWHMx, FWHMy, WEIGHT, DIVx, DIVy, COVx, COVy
        """
        if cols == 7:
            header = "*ENERGY(GEV) SigmaT0(GEV) X(CM)   Y(CM)    FWHMx(cm) FWHMy(cm) WEIGHT\n"
        elif cols == 6:
            header = "*ENERGY(GEV) X(CM)   Y(CM)    FWHMx(cm) FWHMy(cm) WEIGHT\n"
        elif cols == 5:
            header = "*ENERGY(GEV) X(CM)   Y(CM)    FWHMx(cm) FWHMy(cm) WEIGHT\n"
        else:
            raise ValueError(f"Output format with {cols} columns is not supported.")

        for i, myfield in enumerate(self.fields):
            j = i + 1  # j is the field number, i is the field index.
            output = header
            # in case all fields should be written to disk, build a new filename with _XX added to the stem
            # of the filename, based on the field number (not the filed index), i.e. first file is sobp_01.dat
            if field_nr == 0:
                fout = Path(fn.parent, (f"{fn.stem}_{j:02d}{fn.suffix}"))
            else:
                # otherwise, check if this is a field the user wanted, if not, skip it.
                fout = fn
                if (j) != field_nr:
                    continue

            for layer in myfield.layers:

                # DICOM and PLD sometimes have empty layers. This will be skipped, to not clutter the sobp.dat file.
                if layer.is_empty:
                    continue

                # Do some conversions, since sobp.dat hold different units.
                energy = layer.energy_measured * 0.001  # convert MeV -> GeV
                espread = layer.espread * 0.001  # convert MeV -> GeV

                # Check if field-flip was requested. Then do so for FWHMxy and spot positions
                if self.flip_xy:
                    fwhmy, fwhmx = layer.spotsize * 0.1  # mm -> cm
                else:
                    fwhmx, fwhmy = layer.spotsize * 0.1  # mm -> cm

                for spot in layer.spots:
                    if self.flip_xy:
                        xpos = spot[1] * 0.1  # mm -> cm
                        ypos = spot[0] * 0.1  # mm -> cm
                    else:
                        xpos = spot[0] * 0.1  # mm -> cm
                        ypos = spot[1] * 0.1  # mm -> cm

                    wt = spot[3]
                    # format output file. Carefully tuned so they appear in nice columns synced to header. Maybe.
                    if cols == 7:
                        s = f"{energy:8.6f}     {espread:10.8f}  " \
                            + f"{xpos:6.2f}   {ypos:6.2f}  " \
                            + f"{fwhmx:6.2f}   {fwhmy:6.2f}     {wt:10.4e}\n"
                    elif cols == 6:
                        s = f"{energy:8.6f}     " \
                            + f"{xpos:6.2f}   {ypos:6.2f}  " \
                            + f"{fwhmx:6.2f}   {fwhmy:6.2f}     {wt:10.4e}\n"
                    else:
                        s = f"{energy:8.6f}     " \
                            + f"{xpos:6.2f}   {ypos:6.2f}  " \
                            + f"{fwhmx:6.2f}   {wt:10.4e}\n"
                    output += s
            logger.debug("Export field %d %s, %g MeV", j, fout, myfield.layers[0].energy_nominal)
            fout.write_text(output)  # still in field loop, output for every field


def load(file: Path, beam_model: BeamModel, scaling: float, flip_xy: bool) -> Plan:
    """Load file, autodiscovery by suffix."""
    logger.debug("load() autodiscovery %s", file)
    ext = file.suffix.lower()  # extract suffix, incl. dot separator

    if ext == ".pld":
        logger.debug("autodiscovery: Found a IBA pld file.")
        p = load_PLD_IBA(file, scaling)
    elif ext == ".dcm":
        logger.debug("autodiscovery: Found a DICOM file.")
        p = load_DICOM_VARIAN(file, scaling)  # so far I have no other dicom files
    elif ext == ".rst":
        logger.debug("autodiscovery: Found a GSI raster scan file.")
        p = load_RASTER_GSI(file, scaling)
    else:
        raise ValueError(f"autodiscovery: Unknown file type. {file}")

    # apply beam model if available
    if beam_model:
        p.beam_model = beam_model
    else:
        logger.debug("BeamModel is unavailable in Plan.")

    p.apply_beammodel()
    p.flip_xy = flip_xy

    return p


def load_PLD_IBA(file_pld: Path, scaling=1.0) -> Plan:
    """
    Load a IBA-style PLD-file.

    file_pld : a file pointer to a .pld file, opened for reading.
    Here we assume there is only a single field in every .pld file.
    """
    eps = 1.0e-10

    current_plan = Plan()

    myfield = Field()  # avoid collision with dataclasses.field
    current_plan.fields = [myfield]
    current_plan.n_fields = 1

    # p.factor holds the number of particles * dE/dx / MU = some constant
    # p.factor = 8.106687e7  # Calculated Nov. 2016 from Brita's 32 Gy plan. (no dE/dx)
    current_plan.factor = 5.1821e8  # protons per (MU/dEdx), Estimated calculation Apr. 2017 from Brita's 32 Gy plan.

    # currently scaling is treated equal at plan and field level. This is for future use.
    current_plan.scaling = scaling
    field.scaling = scaling

    pldlines = file_pld.read_text().split('\n')
    pldlen = len(pldlines)
    logger.info("Read %d lines of data.", pldlen)

    field.layers = []
    field.n_layers = 0

    # First line in PLD file contains both plan and field data
    tokens = pldlines[0].split(",")
    current_plan.patient_id = tokens[1].strip()
    current_plan.patient_name = tokens[2].strip()
    current_plan.patient_initals = tokens[3].strip()
    current_plan.patient_firstname = tokens[4].strip()
    current_plan.plan_label = tokens[5].strip()
    current_plan.beam_name = tokens[6].strip()
    field.cmu = float(tokens[7].strip())  # total amount of MUs in this field
    field.pld_csetweight = float(tokens[8].strip())
    field.n_layers = int(tokens[9].strip())  # number of layers

    espread = 0.0  # will be set by beam model

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
            # IBA PLD holds nominal spot size in 1D, 1 sigma in [mm]
            spotsize = float(tokens[1].strip()) * s2fwhm  # convert mm sigma to mm FWHM (this is just a float)

            energy_nominal = float(tokens[2].strip())
            cmu = float(tokens[3].strip())
            nspots = int(tokens[4].strip())
            logger.debug(tokens)

            # read number of repaints only if 5th column is present, otherwise set to 0
            nrepaint = 0  # we suspect repaints = 1 means all dose will be delivered once.
            if len(tokens) > 5:
                nrepaint = int(tokens[5].strip())

            spots = np.array([])

            layer = Layer(spots=spots,
                          spotsize=np.array([spotsize, spotsize]),
                          energy_nominal=energy_nominal,
                          energy_measured=energy_nominal,
                          espread=espread,
                          cum_mu=cmu,
                          n_spots=nspots,
                          repaint=nrepaint)

            for element in elements:  # loop over each spot in this layer
                token = element.split(",")
                # the .pld file has every spot position repeated, but MUs are only in
                # every second line, for reasons unknown.
                _x = float(token[1].strip())
                _y = float(token[2].strip())
                _mu = float(token[3].strip())

                # fix bad float conversions
                if np.abs(_x) < eps:
                    _x = 0.0
                if np.abs(_y) < eps:
                    _y = 0.0
                if _mu < eps:
                    _mu = 0.0

                # PLD files have the spots listed tiwce, once with no MUs. These are removed here.
                if _mu > 0.0:
                    layer.spots = np.append([layer.spots], [_x, _y, _mu, _mu])
                else:
                    # this was an empty spot, decrement spot count, and do not add it.
                    nspots -= 1

            layer.spots = layer.spots.reshape(nspots, 4)
            current_plan.fields[0].layers.append(layer)

            logger.debug("appended layer %i with %i spots", len(current_plan.fields[0].layers), layer.n_spots)
    return current_plan


def load_DICOM_VARIAN(file_dcm: Path, scaling=1.0) -> Plan:
    """Load varian type dicom plans."""
    ds = dicom.dcmread(file_dcm)
    # Total number of energy layers used to produce SOBP

    p = Plan()
    p.patient_id = ds['PatientID'].value
    p.patient_name = ds['PatientName'].value
    p.patient_initals = ""
    p.patient_firstname = ""
    p.plan_label = ds['RTPlanLabel'].value
    p.plan_date = ds['RTPlanDate'].value

    # protons per (MU/dEdx), Estimated calculation Nov. 2022 from DCPT beam model
    p.factor = 17247566.1
    p.scaling = scaling  # nee note in IBA reader above.
    espread = 0.0  # will be set by beam model
    p.n_fields = int(ds['FractionGroupSequence'][0]['NumberOfBeams'].value)
    logger.debug("Found %i fields", p.n_fields)

    dcm_fgs = ds['FractionGroupSequence'][0]['ReferencedBeamSequence']  # fields for given group number

    for i, dcm_field in enumerate(dcm_fgs):
        myfield = Field()
        logger.debug("Appending field number %d...", i)
        p.fields.append(myfield)
        myfield.dose = float(dcm_field['BeamDose'].value)
        myfield.cum_mu = float(dcm_field['BeamMeterset'].value)
        myfield.pld_csetweight = 1.0
        myfield.scaling = scaling  # nee note in IBA reader above.
        myfield.n_layers = int(ds['IonBeamSequence'][i]['NumberOfControlPoints'].value)
        dcm_ibs = ds['IonBeamSequence'][i]['IonControlPointSequence']  # layers for given field number
        logger.debug("Found %i layers in field number %i", myfield.n_layers, i)

        cmu = 0.0

        for j, layer in enumerate(dcm_ibs):

            # gantry and couch angle is stored per energy layer, strangely
            if 'NominalBeamEnergy' in layer:
                energy = float(layer['NominalBeamEnergy'].value)  # Nominal energy in MeV
            if 'NumberOfScanSpotPositions' in layer:
                nspots = int(layer['NumberOfScanSpotPositions'].value)  # number of spots
                logger.debug("Found %i spots in layer number %i at energy %f", nspots, j, energy)
            if 'NumberOfPaintings' in layer:
                nrepaint = int(layer['NumberOfPaintings'].value)  # number of spots
            if 'ScanSpotPositionMap' in layer:
                _pos = np.array(layer['ScanSpotPositionMap'].value).reshape(nspots, 2)  # spot coords in mm
            if 'ScanSpotMetersetWeights' in layer:
                _mu = np.array(layer['ScanSpotMetersetWeights'].value).reshape(nspots, 1)  # spot MUs
                cmu = _mu.sum()
            if 'ScanningSpotSize' in layer:
                # Varian dicom holds nominal spot size in 2D, FWHMMx,y in [mm]
                spotsize = np.array(layer['ScanningSpotSize'].value)
                spots = np.c_[_pos, _mu, _mu]  # weight will be calculated later when beam model is applied
                myfield.layers.append(Layer(spots, spotsize, energy, energy, espread, cmu, nrepaint, nspots))
    return p


def load_RASTER_GSI(file_rst: Path, scaling=1.0):
    """this is implemented in pytrip, maybe we could import it?."""
    logging.warning("GSI raster file reader not implemented yet.")
    logging.info("Opening file %s", file_rst)
    p = Plan()
    p.scaling = scaling  # nee note in IBA reader above.
    return p


def main(args=None) -> int:
    """
    Read a plan file (dicom, pld, rst), and convert it to a spot list, easy to read by MC codes.

    The MU based spot list in dicom/pld/rst is converted to particle weighted spot list,
    optionally based on a realistic beam model, or on simple estimations.
    """
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('fin',
                        metavar="input_file",
                        type=Path,
                        help="path to input file in IBA '.pld'-format or Varian DICOM-RN.")
    parser.add_argument('fout',
                        nargs='?',
                        metavar="output_file",
                        type=Path,
                        help="path to the SHIELD-HIT12A/FLUKA output_file. Default: 'sobp.dat'",
                        default="sobp.dat")
    parser.add_argument('-b',
                        metavar="beam_model.csv",
                        type=Path,
                        help="optional input beam model in commasparated CSV format",
                        dest='fbm',
                        default=None)
    parser.add_argument('-i', '--invert', action='store_true', help="invert XY axis", dest="invert", default=False)
    parser.add_argument('-f',
                        '--field',
                        type=int,
                        dest='field_nr',
                        help="select which field to export, for dicom files holding several fields. " +
                        "'0' will produce multiple output files with a running number.",
                        default=1)
    parser.add_argument('-d',
                        '--diag',
                        action='store_true',
                        help="print diagnostics, but do not export data",
                        dest="diag",
                        default=False)
    parser.add_argument('-s', '--scale', type=float, dest='scale', help="number of particles*dE/dx per MU", default=1.0)
    parser.add_argument('-c',
                        '--columns',
                        type=int,
                        dest='cols',
                        help="number of columns in output file. 5, 6, 7 col format supported, default is 7.",
                        default=7)
    parser.add_argument('-v', '--verbosity', action='count', help="increase output verbosity", default=0)
    parser.add_argument('-V', '--version', action='version', version=pymchelper.__version__)
    parsed_args = parser.parse_args(args)

    if parsed_args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)

    if parsed_args.verbosity > 1:
        logging.basicConfig(level=logging.DEBUG)

    if parsed_args.fbm:
        bm = BeamModel(parsed_args.fbm)
    else:
        bm = None

    pln = load(parsed_args.fin, bm, parsed_args.scale, parsed_args.invert)

    if parsed_args.diag:
        pln.diagnose()
    else:
        pln.export(parsed_args.fout, parsed_args.cols, parsed_args.field_nr)

    return 0


if __name__ == '__main__':
    # Run sys.exit with exit code of the main method.
    sys.exit(main(sys.argv[1:]))
