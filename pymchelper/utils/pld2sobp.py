"""
Reads PLD file in IBA format and convert to sobp.dat
which is readable by FLUKA with source_sampler.f and by SHIELD-HIT12A.

Output file, sobp.dat is a text file.
Comment lines start with *.
It may have 5,6 or 7 columns.
These columns can be:

  - 5 columns: E, X, Y, FWHM, W
  - 6 columns: E, X, Y, FWHM_X, FWHM_Y, W
  - 7 columns: E, DE, X, Y, FWHM_X, FWHM_Y, W

where:

  - E : kinetic energy in GeV/amu
  - DE : energy spread (sigma) in GeV/amu
  - X, Y : position (in cm) of the beamlet/spot center
  - FWHM_X, FWHM_Y, FWHM : spot size (in cm)

All above-mentioned quantities are defined at beam source location (typically nozzle exit)

For more details, see SHIELD-HIT12A manual http://shieldhit.org/index.php?id=documentation

TODO: Translate energy to spotsize.
"""
import argparse
import json
import logging
from math import exp, log
import sys

logger = logging.getLogger(__name__)


def dedx_air(energy_MeV):
    """
    Calculate the mass stopping power of protons in air following ICRU 49.
    Valid from 1 to 500 MeV only.

    :params energy: Proton energy in MeV
    :returns: mass stopping power in MeV cm2/g
    """
    if energy_MeV > 500.0 or energy_MeV < 1.0:
        logger.error("Proton energy must be between 1 and 500 MeV.")
        raise ValueError("Energy = {:.2f} out of bounds.".format(energy_MeV))

    x = log(energy_MeV)
    y = 5.4041 - 0.66877 * x - 0.034441 * (x ** 2) - 0.0010707 * (x ** 3) + 0.00082584 * (x ** 4)
    return exp(y)


def air_scat(length_cm, energy_MeV, z=1, rest_mass_MeV=938.2723128):
    """
    Returns sigma calculated from scattering angle in air
    Uses Lynch and Dahl approximation
    :param length_cm: scattering path in air in [cm]
    :param energy_MeV: particle kinetic energy in MeV/amu
    :param z: ion charge
    :param rest_mass_MeV: rest mass in MeV/amu
    :return: scattering sigma in cm
    """
    x0_cm = 30390.0  # radiation length of air in [cm]
    cp = ((energy_MeV + rest_mass_MeV) ** 2 - rest_mass_MeV ** 2) ** 0.5
    beta = cp / (energy_MeV + rest_mass_MeV)
    theta0 = (13.6 / (beta * cp)) * z
    theta0 *= (length_cm / x0_cm) ** 0.5 * (1.0 + 0.038 * log(length_cm / x0_cm))
    return 3.0 ** (-0.5) * theta0 * length_cm


def range_air_m(energy_MeV):
    """
    Range in air of protons approximation
    :param energy_MeV: proton kinetic energy in MeV/amu
    :return: range in air in m
    """
    return (energy_MeV / 9.3) ** 1.8


def energy_air(range_m):
    """
    Range in air of protons approximation
    :param range_m: range in air in m
    :return: proton kinetic energy in MeV/amu
    """
    return 9.3 * range_m ** (1.0 / 1.8)


class Layer(object):
    """
    Class for handling Layers.
    """

    def __init__(self, spottag, energy, meterset, elsum, repaints, elements):
        self.spottag = float(spottag)  # spot tag number
        self.energy = float(energy)
        self.meterset = float(meterset)  # MU sum of this + all previous layers
        self.elsum = float(elsum)  # sum of elements in this layer
        self.repaints = int(repaints)  # number of repaints
        self.elements = elements  # number of elements
        self.spots = int(len(elements) / 2)  # there are two elements per spot

        self.x = [0.0] * self.spots  # position of spot center at isocenter [mm]
        self.y = [0.0] * self.spots  # position of spot center at isocenter [mm]
        self.w = [0.0] * self.spots  # MU weight
        self.rf = [0.0] * self.spots  # fluence weight

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

                self.layers.append(Layer(token[1].strip(),  # spot tag
                                         token[2].strip(),  # energy
                                         token[3].strip(),  # cumulative meter set weight including this layer
                                         token[4].strip(),  # number of elements in this layer
                                         repaints_no,  # number of repaints.
                                         elements))  # array holding all elements for this layer


def extract_model(model_dictionary, spottag, energy):
    """
    TODO
    :param model_dictionary:
    :param spottag:
    :param energy:
    :return:
    """

    sigma_to_fwhm = (8.0 * log(2.0)) ** 0.5

    spot_fwhm_x_cm = 0.0  # point-like source
    spot_fwhm_y_cm = 0.0  # point-like source
    energy_spread = 0.0

    if model_dictionary:
        compatible_models = [model for model in model_dictionary["model"] if spottag == model["spottag"]]
        if not compatible_models:
            print("no models found for spottag {}".format(spottag))
            return None
        elif len(compatible_models) > 1:
            print("more than one model found for spottag {}, taking first one".format(spottag))
        else:
            compatible_layers = [model_layer for model_layer in compatible_models[0]["layers"] if
                                 model_layer["mean_energy"] == energy]
            if not compatible_layers:
                print("no layers found for {}".format(energy))
                return None
            elif len(compatible_models) > 1:
                print("more than one layer found for {}, taking first one".format(energy))
            else:
                spot_fwhm_x_cm = sigma_to_fwhm * compatible_layers[0]["spot_x"]
                spot_fwhm_y_cm = sigma_to_fwhm * compatible_layers[0].get("spot_y", spot_fwhm_x_cm)
                energy_spread = compatible_layers[0].get("energy_spread", 0.0)
    return spot_fwhm_x_cm, spot_fwhm_y_cm, energy_spread


def main(args=sys.argv[1:]):
    """ Main function of the pld2sobp script.
    """

    import pymchelper

    # _scaling holds the number of particles * dE/dx / MU = some constant
    _scaling = 5e8  # some rough estimation for typical proton center

    parser = argparse.ArgumentParser()
    parser.add_argument('fin', metavar="input_file.pld", type=argparse.FileType('r'),
                        help="path to .pld input file in IBA format.",
                        default=sys.stdin)
    parser.add_argument('fout', nargs='?', metavar="output_file.dat", type=argparse.FileType('w'),
                        help="path to the SHIELD-HIT12A/FLUKA output file, or print to stdout if not given.",
                        default=sys.stdout)
    parser.add_argument('-m', '--model', metavar='beam_model.yml', type=argparse.FileType('r'),
                        help="beam model file",
                        default=None)
    parser.add_argument('-a', '--sad', type=float, dest='sad',
                        help="distance from beam virtual source to isocenter [cm]", default=0.0)
    parser.add_argument('-n', '--nozzle', type=float, dest='nozzle', required=True,
                        help="distance from nozzle to isocenter [cm]")
    parser.add_argument('-b', '--mc_source', type=float, dest='mc_source',
                        help="distance from MC source to isocenter [cm]", default=0.0)
    parser.add_argument('-x', '--spotsize_x', type=float, dest='spotsize_x',
                        help="X spot size at isocenter in [cm]", default=0.0)
    parser.add_argument('-y', '--spotsize_y', type=float, dest='spotsize_y',
                        help="Y spot size at isocenter in [cm]", default=0.0)
    parser.add_argument('-e', '--deltae', type=float, dest='deltae',
                        help="energy spread (sigma) in [GeV]", default=0.0)
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

    print(args)

    pld_data = PLDRead(args.fin)
    args.fin.close()

    delta_e_present = False
    fwhm_y_present = False

    if args.spotsize_y > 0 or args.model:
        fwhm_y_present = True

    if args.deltae > 0 or args.model:
        delta_e_present = True

    if args.mc_source == 0:
        args.mc_source = args.nozzle

    print(args)
    # logger.info("Setting MC source location to the default value {:10.3f} [cm]".format(args.mc_source))

    number_of_columns = 5
    header_line = "*ENERGY(GEV) X(CM) Y(CM) FWHM(cm) WEIGHT\n"
    data_format = "{:-10.6f} {:-10.2f} {:-10.2f} {:-10.2f} {:-16.6E}\n"
    if fwhm_y_present:
        number_of_columns = 6
        header_line = "*ENERGY(GEV) X(CM) Y(CM) FWHMx(cm) FWHMy(cm) WEIGHT\n"
        data_format = "{:-10.6f} {:-10.2f} {:-10.2f} {:-10.2f} {:-10.2f} {:-16.6E}\n"
    if delta_e_present:
        number_of_columns = 7
        header_line = "*ENERGY(GEV) SigmaT0(GEV) X(CM) Y(CM) FWHMx(cm) FWHMy(cm) WEIGHT\n"
        data_format = "{:-10.6f} {:-10.6f} {:-10.2f} {:-10.2f} {:-10.2f} {:-10.2f} {:-16.6E}\n"

    beam_model = None
    if args.model:
        # TODO add validation of JSON schema
        beam_model = json.load(args.model)

    meterset_weight_sum = 0.0
    particles_sum = 0.0

    args.fout.writelines(header_line)
    for layer in pld_data.layers:

        model_data = extract_model(beam_model, layer.spottag, layer.energy)

        if model_data:
            spot_fwhm_x_cm, spot_fwhm_y_cm, energy_spread = model_data
        else:
            return

        energy_nozzle_GeV = layer.energy * 0.001  # MeV -> GeV
        delta_e_nozzle_GeV = 0.0
        range_change_m = args.nozzle - args.mc_source

        for spot_x_iso_mm, spot_y_iso_mm, spot_w, spot_rf in zip(layer.x, layer.y, layer.w, layer.rf):

            weight = spot_rf * pld_data.mu / pld_data.csetweight
            # Need to convert to weight by fluence, rather than weight by dose
            # for building the SOBP. Monitor Units (MU) = "meterset", are per dose
            # in the monitoring Ionization chamber, which returns some signal
            # proportional to dose to air. D = phi * S => MU = phi * S(air)
            phi_weight = weight / dedx_air(layer.energy)

            # add number of particles in this spot
            particles_spot = args.scale * phi_weight
            particles_sum += particles_spot

            meterset_weight_sum += spot_w

            if args.sad != 0:
                spot_x_source_cm = spot_x_iso_mm * 0.1 * (args.sad - args.mc_source) / args.sad
                spot_y_source_cm = spot_y_iso_mm * 0.1 * (args.sad - args.mc_source) / args.sad
            else:
                spot_x_source_cm = spot_x_iso_mm * 0.1
                spot_y_source_cm = spot_y_iso_mm * 0.1

            layer_xy_source_cm = [spot_x_source_cm, spot_y_source_cm]

            # TODO FWHM conversion
            spot_at_isoc_dist_cm = 0.1 * (spot_x_iso_mm ** 2 + spot_x_iso_mm ** 2) ** 0.5

            if args.sad != 0:
                # spot_at_nozzle_dist_cm = spot_at_isoc_dist_cm * (args.sad - args.nozzle) / args.sad
                spot_at_mc_source_dist_cm = spot_at_isoc_dist_cm * (args.sad - args.mc_source) / args.sad
            else:
                # spot_at_nozzle_dist_cm = spot_at_isoc_dist_cm
                spot_at_mc_source_dist_cm = spot_at_isoc_dist_cm

            # TODO energy conversion
            if range_change_m == 0:
                energy_mc_source_GeV = energy_nozzle_GeV
            else:
                energy_mc_source_GeV = energy_air(range_air_m(energy_nozzle_GeV) - range_change_m)

            if args.sad != 0:
                air_length_cm = (spot_at_isoc_dist_cm ** 2 + args.sad ** 2) ** 0.5
                air_length_cm -= (spot_at_mc_source_dist_cm ** 2 + (args.sad - args.mc_source) ** 2) ** 0.5
                air_scat_sigma_cm = air_scat(air_length_cm, energy_MeV=energy_nozzle_GeV * 1e3)
                print(air_scat_sigma_cm)

            if args.flip:
                layer_xy_source_cm.reverse()

            if number_of_columns == 7:

                # TODO energy conversion
                delta_e_mc_source_GeV = delta_e_nozzle_GeV

                args.fout.writelines(data_format.format(energy_mc_source_GeV,
                                                        delta_e_mc_source_GeV,
                                                        layer_xy_source_cm[0],
                                                        layer_xy_source_cm[1],
                                                        spot_fwhm_x_cm,  # FWHMx
                                                        spot_fwhm_y_cm,  # FWHMy
                                                        particles_spot))
            elif number_of_columns == 6:
                args.fout.writelines(data_format.format(energy_mc_source_GeV,
                                                        layer_xy_source_cm[0],
                                                        layer_xy_source_cm[1],
                                                        spot_fwhm_x_cm,  # FWHMx
                                                        spot_fwhm_y_cm,  # FWHMy
                                                        particles_spot))
            elif number_of_columns == 5:
                args.fout.writelines(data_format.format(energy_mc_source_GeV,
                                                        layer_xy_source_cm[0],
                                                        layer_xy_source_cm[1],
                                                        spot_fwhm_x_cm,
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
