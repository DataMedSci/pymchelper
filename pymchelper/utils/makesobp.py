"""
Reads PLD file in IBA format and convert to sobp.dat
which is readable by FLUKA with source_sampler.f and by SHIELD-HIT12A.

TODO: Translate energy to spotsize.
"""
import sys
import logging
import argparse
# from math import exp, log

logger = logging.getLogger(__name__)


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

    print(dir(args.fin))
    print(args.fin.name)
    args.fin.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
