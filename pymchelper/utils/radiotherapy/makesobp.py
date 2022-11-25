"""
Read particle therapy treatment plans, and convert them to a generic format which can be read by MC codes.

Source files may be
- in IBA .pld fileformat
- in Varian .dcm DICOM format
- TODO: GSI .rst RasterScan format

Resulting file is readable by FLUKA with source_sampler.f and by SHIELD-HIT12A.
DICOM file may carry several fields, in that case, multiple output files will be generated with field number added
to the filename.
"""
import sys
import logging
import argparse

logger = logging.getLogger(__name__)


def write_sobp(pp, fout, ncols=6):  # TODO, input filename instead, since several output files may have to be openend
    """
    Formats options for SHIELD-HIT
    5 columns: ENERGY, X, Y, FWHM, WEIGHT
    6 columns: ENERGY, X, Y, FWHMx, FWHMy, WEIGHT
    7 columns: ENERGY, ESPREAD, X, Y, FWHMx, FWHMy, WEIGHT
    11 columns: ENERGY, ESPREAD, X, Y, FWHMx, FWHMy, WEIGHT, DIVx, DIVy, COVx, COVy

    Details:
        ENERGY: Kinetic energy in [GeV/nucleon] (Note, nucleon is an integer number)
        ESPREAD: 1 sigma spread in kinetic energy [GeV/nucleon]
        X, Y: x- or y-position in [cm]
        FWHMx,y: Full width half maximum of spot in [cm]. (5 column format assumes a round spot)
        WEIGHT: particle weight, either relative or actual number of particles delivered.
        DIVx,y:
        COVx,y:d
    """
    if ncols == 5:
        outstr = "{:-10.6f} {:-10.2f} {:-10.2f} {:-10.2f} {:-16.6E}\n"
    if ncols == 6:
        outstr = "{:-10.6f} {:-10.2f} {:-10.2f} {:-10.2f} {:-10.2f} {:-16.6E}\n"
    if ncols == 7:
        outstr = "{:-10.6f} {:-16.6E} {:-10.2f} {:-10.2f} {:-10.2f} {:-10.2f} {:-16.6E}\n"
    if ncols == 11:
        outstr = "{:-10.6f} {:-16.6E} {:-10.2f} {:-10.2f} {:-10.2f} {:-10.2f} {:-16.6E}\n"
        outstr += "{:-10.2f} {:-10.2f} {:-10.2f} {:-10.2f}"

    for i, field in enumerate(pp.fields):

        for layer in field.layers:
            for spot in layer.spots:
                # for spot_x, spot_y, spot_w, spot_rf in zip(layer.x, layer.y, layer.w, layer.rf):
                fout.writelines(outstr.format(layer.energy * 0.001,  # MeV -> GeV
                                              spot[0], spot[1],
                                              field.spotsize,
                                              spot[3]))

    logger.info("Data were scaled with a factor of {:e} particles*S/MU.".format(pp.scaleing))
    if pp.flip_xy:
        logger.info("Output file was XY flipped.")


def main(args=None):
    """Main function of the pld2sobp script."""
    if args is None:
        args = sys.argv[1:]

    import pymchelper
    import pymchelper.utils.radiotherapy.plan as plan

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
        bm = plan.load_beammodel(args.fbm.name)
    else:
        bm = None

    pln = pp.load(args.fin, bm, args.scale, args.flip)
    args.fin.close()
    logger.debug(pln)

    write_sobp(pln, args.fout)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
