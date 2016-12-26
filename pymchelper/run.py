#!/usr/bin/env python

import glob
import logging
import sys

import argparse

from pymchelper.detector import merge_list, merge_many, Converters, ErrorEstimate
from pymchelper.writers.plots import ImageWriter

logger = logging.getLogger(__name__)


def set_logger_level(args):
    if args.quiet:
        if args.quiet == 1:
            level = "WARNING"
        if args.quiet == 2:
            level = "ERROR"
        else:
            level = "CRITICAL"
    elif args.verbose:
        level = "DEBUG"
    else:
        level = "INFO"
    logging.basicConfig(level=level)


def add_default_options(parser):
    import pymchelper
    parser.add_argument("input", help='input filename, file list or pattern', type=str)
    parser.add_argument("output", help='output filename or directory', nargs='?')
    parser.add_argument("--many", help='automatically merge data from various sources', action="store_true")
    parser.add_argument("--nan", help='ignore NaN in averaging', action="store_true")
    parser.add_argument("--error",
                        help='type of error estimate to add (default: ' + ErrorEstimate.stderr.name + ')',
                        default=ErrorEstimate.stderr.name,
                        choices=[x.name for x in ErrorEstimate],
                        type=str)
    parser.add_argument("-n", '--nscale', help='scale with number of primaries N.', default=1, type=float)
    parser.add_argument('-v',
                        '--verbose',
                        action='count',
                        default=0,
                        help='give more output. Option is additive, and can be used up to 3 times')
    parser.add_argument('-q', '--quiet', action='count', default=0, help='be silent')
    parser.add_argument('-V', '--version', action='version', version=pymchelper.__version__)


def main(args=sys.argv[1:]):
    import pymchelper
    import os

    _progname = os.path.basename(sys.argv[0])
    _helptxt = 'Universal converter for FLUKA and SHIELD-HIT12A generated files.'
    _epitxt = '''Type '{:s} <converter> --help' for help on a specific converter.'''.format(_progname)

    parser = argparse.ArgumentParser(description=_helptxt, epilog=_epitxt)

    # subparsers = parser.add_subparsers(title='available converters', metavar='...')
    subparsers = parser.add_subparsers(dest='command', metavar='converter')

    parser_txt = subparsers.add_parser(Converters.txt.name, help='converts to plain txt file')
    add_default_options(parser_txt)

    parser_image = subparsers.add_parser(Converters.image.name, help='converts to PNG images')
    add_default_options(parser_image)
    parser_image.add_argument("--colormap",
                              help='image color map, see http://matplotlib.org/users/colormaps.html '
                                   'for list of possible options (default: ' + ImageWriter.default_colormap + ')',
                              default=ImageWriter.default_colormap,
                              type=str)

    parser_plotdata = subparsers.add_parser(Converters.plotdata.name, help='converts to gnuplot data')
    add_default_options(parser_plotdata)

    parser_gnuplot = subparsers.add_parser(Converters.gnuplot.name, help='converts to gnuplot script')
    add_default_options(parser_gnuplot)

    parser_tripcube = subparsers.add_parser(Converters.tripcube.name, help='converts to trip98 data cube')
    add_default_options(parser_tripcube)

    parser_tripddd = subparsers.add_parser(Converters.tripddd.name, help='converts to trip98 ddd file')
    add_default_options(parser_tripddd)
    parser_tripddd.add_argument("--energy",
                                help='energy of the beam [MeV/amu]',
                                type=float)
    parser_tripddd.add_argument("--ngauss",
                                help='number of Gauss curves to fit (default: 2)',
                                choices=(0, 1, 2),
                                default=2,
                                type=int)

    parser.add_argument('-V', '--version', action='version', version=pymchelper.__version__)

    parsed_args = parser.parse_args(args)

    if parsed_args.command is not None:
        set_logger_level(parsed_args)

        # check if output directory exists
        if parsed_args.output is not None:
            output_dir = os.path.dirname(parsed_args.output)
            if output_dir and not os.path.exists(output_dir):
                raise IOError("Directory {}/ does not exist.".format(output_dir))

        # TODO add filename discovery
        files = sorted(glob.glob(parsed_args.input))
        if not files:
            logger.error('File does not exist: ' + parsed_args.input)

        parsed_args.error = ErrorEstimate[parsed_args.error]

        if parsed_args.many:
            merge_many(files, parsed_args.output, parsed_args)
        else:
            merge_list(files, parsed_args.output, parsed_args)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
