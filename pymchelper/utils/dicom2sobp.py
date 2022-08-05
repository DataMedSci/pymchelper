import sys
import logging
import argparse
import pydicom as dicom

import numpy as np
from scipy.interpolate import interp1d

logger = logging.getLogger(__name__)

s2fwhm = 2.0 * np.sqrt(2.0 * np.log(2.0))  # 1 FWHM = 2.355 * sigma


class BeamModel():
    """
    Beam model from a given CSV file
    """

    def __init__(self, fn, nominal=True):
        """
        Loads a beam model given as a CSV file.
        Interpolation lookup can be done as a function of nominal energy (defualt, nominal=True),
        or as a function of actual energy (nominal=False).
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


class Spot():
    """
    """

    def __init__(self, spotnr, layernr, energy, mu, x, y):
        """
        """
        self.spotnr = spotnr  # spot number
        self.layernr = layernr  # spot number
        self.energy = energy  # nominal energy
        self.mu = mu   # Monitor units
        self.x = x  # x position [cm]
        self.y = y  # y position [cm]


class Plan():
    """
    Plan from a given dicom file
    """

    def __init__(self, fn):
        """
        """
        ds = dicom.dcmread(fn)
        # Total number of energy layers used to produce SOBP
        NoLayer = len(ds['IonBeamSequence'][0]['IonControlPointSequence'].value)
        # Total Dose
        Dose = float(ds['FractionGroupSequence'][0]['ReferencedBeamSequence'][0]['BeamDose'].value)
        # Array used to store all/final data extracted from the dicom file
        CompleteData = np.array([])
        LayerEnergy = 0
        LayerNumber = 0

        for i in range(NoLayer):
            NominalEnergy = ds['IonBeamSequence'][0]['IonControlPointSequence'][i]['NominalBeamEnergy'].value
            NoPosition = ds['IonBeamSequence'][0]['IonControlPointSequence'][i]['NumberOfScanSpotPositions'].value
            position = np.array(ds['IonBeamSequence'][0]['IonControlPointSequence'][i]['ScanSpotPositionMap'].value)
            data = position.reshape(NoPosition, 2)

            if (LayerEnergy != NominalEnergy):
                LayerEnergy = NominalEnergy
                LayerNumber = LayerNumber + 1

            Layer = np.empty(NoPosition)
            Layer.fill(LayerNumber)
            data = np.insert(data, 0, Layer, axis=1)

            Energy = np.empty(NoPosition)
            Energy.fill(NominalEnergy)
            data = np.insert(data, 1, Energy, axis=1)

            weight = np.array(ds['IonBeamSequence'][0]['IonControlPointSequence'][i]['ScanSpotMetersetWeights'].value)
            data = np.insert(data, 2, weight*Dose, axis=1)

            if (i == 0):
                CompleteData = data
            else:
                CompleteData = np.concatenate((CompleteData, data))

        ZeroMUIndex = []
        for j in range(len(CompleteData)):
            if CompleteData[j, 2] == 0:
                ZeroMUIndex.append(j)

        CompleteData = np.delete(CompleteData, ZeroMUIndex, 0)

        SpotIndex = np.arange(1, len(CompleteData)+1, step=1)
        CompleteData = np.insert(CompleteData, 0, SpotIndex, axis=1)

        self.nspots = len(CompleteData)
        self.spots = [None] * self.nspots

        for i, d in enumerate(CompleteData):
            self.spots[i] = Spot(d[0], d[1], d[2], d[3], d[4], d[5])

    def makesobp(self, bm):
        """
        """
        pass

    def writesobp(self, fn):
        """
        """
        pass


def main(args=sys.argv[1:]):
    """ Main function for makesobp.py
    """
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", help="input treatmentplan")  # , type=argparse.FileType('r'))
    parser.add_argument("-v", "--verbosity", action='count', help="increase output verbosity", default=0)
    parser.add_argument("-f", "--flip-xy", action='store_true', help="flips x-y axis", dest="flipxy", default=False)
    parser.add_argument("-b", "--beam-model", nargs='?', help="CSV beam model", type=argparse.FileType('r'),
                        dest="bmodel")
    parser.add_argument('-o', '--outfile', nargs='?', type=argparse.FileType('w'),
                        help='output file, in SH12A sobp.dat format. Default: "sobp.dat"', default="SOBP_New_Plan.dat")

    parsed_args = parser.parse_args(args)

    if parsed_args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif parsed_args.verbosity > 1:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()

    finp = parsed_args.plan
    binp = parsed_args.bmodel
    fout = parsed_args.outfile

    plan = Plan(finp)
    if binp:
        bm = BeamModel(binp)

    psum = 0.0
    for spot in plan.spots:
        en = spot.energy  # nominal energy

        pn = bm.f_ppmu(en) * spot.mu * 1e6  # number of primaries
        psum += pn

        s = ""
        s += "{:.5f}".format(bm.f_e(en) / 1000.0)  # actual energy [GeV]
        s += " {:.5f}".format(bm.f_espread(en) * bm.f_e(en) / 100.0 / 1000.0)  # 1 sigma energy spread [GeV]

        if parsed_args.flipxy:
            s += " {:.5f}".format(spot.y * 0.1)			  # Spot position y [cm]
            s += " {:.5f}".format(-spot.x * 0.1)		  # Spot position x [cm
            s += " {:.5f}".format(bm.f_sy(en) * s2fwhm * 0.1)     # FWHM y [cm]
            s += " {:.5f}".format(bm.f_sx(en) * s2fwhm * 0.1)     # FWHM x [cm]
            s += " {:.5f}".format(bm.f_divy(en))                  # div y [rad]
            s += " {:.5f}".format(bm.f_divx(en))                  # div x [rad]
            s += " {:.5f}".format(bm.f_covy(en) * 0.1)             # cov y [cm-rad]
            s += " {:.5f}".format(bm.f_covx(en) * 0.1)             # cov x [cm-rad]

        else:
            s += " {:.5f}".format(spot.x * 0.1)                   # Spot position x [cm]
            s += " {:.5f}".format(spot.y * 0.1)                   # Spot position y [cm]
            s += " {:.5f}".format(bm.f_sx(en) * s2fwhm * 0.1)      # FWHM x [cm]
            s += " {:.5f}".format(bm.f_sy(en) * s2fwhm * 0.1)      # FWHM y [cm]
            s += " {:.5f}".format(bm.f_divx(en))                  # div  x [rad]
            s += " {:.5f}".format(bm.f_divy(en))                  # div  y [rad]
            s += " {:.5f}".format(bm.f_covx(en) * 0.1)            # cov  x [cm-rad]
            s += " {:.5f}".format(bm.f_covy(en) * 0.1)            # cov  y [cm-rad]

        # distal edge hack
        if spot.layernr == 1:
            s += " {:.8e}".format(pn * 1.00)     # particle number without factor 1.15
        elif spot.layernr == 2:
            s += " {:.8e}".format(pn * 1.000)     # particle number
        else:
            s += " {:.8e}".format(pn)     # particle number

        s += "\n"

        fout.write(s)

    print("Number of primaries: {:.3e}".format(pn))


if __name__ == '__main__':
    logging.basicConfig()
    sys.exit(main(sys.argv[1:]))
