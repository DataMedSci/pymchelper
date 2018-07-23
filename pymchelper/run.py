#!/usr/bin/env python

import glob
import logging
import sys

import argparse

from pymchelper.detector import ErrorEstimate
from pymchelper.io import convertfrompattern, convertfromlist
from pymchelper.writers.common import Converters
from pymchelper.writers.plots import ImageWriter, PlotAxis

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
    parser.add_argument('input', help='input filename, file list or pattern', type=str)
    parser.add_argument('output', help='output filename or directory', nargs='?')
    parser.add_argument('-j', '--jobs', help='number of parallel jobs to use (-1 means all CPUs)', default=-1, type=int)
    parser.add_argument('--many', help='automatically merge data from various sources', action="store_true")
    parser.add_argument('-a', '--nan', help='ignore NaN in averaging', action="store_true")
    parser.add_argument('-e', '--error',
                        help='type of error estimate to add (default: ' + ErrorEstimate.stderr.name + ')',
                        default=ErrorEstimate.stderr.name,
                        choices=[x.name for x in ErrorEstimate],
                        type=str)
    parser.add_argument('-n', '--nscale', help='scale with number of primaries N.', default=1, type=float)
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
    axis_names = [x.name for x in PlotAxis]
    parser_image.add_argument('-l', '--log',
                              help='set logscale for plot axis',
                              nargs='+',
                              choices=axis_names,
                              default={},
                              type=str)
    parser_image.add_argument("--colormap",
                              help='image color map, see http://matplotlib.org/users/colormaps.html '
                                   'for list of possible options (default: ' + ImageWriter.default_colormap + ')',
                              default=ImageWriter.default_colormap,
                              type=str)

    parser_excel = subparsers.add_parser(Converters.excel.name, help='converts to MS Excel file')
    add_default_options(parser_excel)

    parser_plotdata = subparsers.add_parser(Converters.plotdata.name, help='converts to gnuplot data')
    add_default_options(parser_plotdata)

    parser_gnuplot = subparsers.add_parser(Converters.gnuplot.name, help='converts to gnuplot script')
    add_default_options(parser_gnuplot)

    parser_inspect = subparsers.add_parser(Converters.inspect.name, help='prints metadata')
    add_default_options(parser_inspect)
    parser_inspect.add_argument('-d', '--details',
                                help='print detailed information about data attribute',
                                action="store_true")

    parser_sparse = subparsers.add_parser(Converters.sparse.name, help='converts to sparse matrix format')
    add_default_options(parser_sparse)
    parser_sparse.add_argument("--threshold",
                               help='only values greater than threshold are saved',
                               type=float,
                               default=0.0)

    parser_tripcube = subparsers.add_parser(Converters.tripcube.name, help='converts to trip98 data cube')
    add_default_options(parser_tripcube)

    parser_tripddd = subparsers.add_parser(Converters.tripddd.name, help='converts to trip98 ddd file')
    add_default_options(parser_tripddd)
    parser_tripddd.add_argument("--energy",
                                help='energy of the beam [MeV/amu] (0 to guess from data)',
                                type=float)
    parser_tripddd.add_argument("--projectile",
                                help='projectile (0 to guess from data)',
                                type=str)
    parser_tripddd.add_argument("--ngauss",
                                help='number of Gauss curves to fit (default: 2)',
                                choices=(0, 1, 2),
                                default=2,
                                type=int)

    parser.add_argument('-V', '--version', action='version', version=pymchelper.__version__)

    parsed_args = parser.parse_args(args)

    status = 0
    if parsed_args.command is not None:
        set_logger_level(parsed_args)

        # TODO add filename discovery
        files = sorted(glob.glob(parsed_args.input))
        if not files:
            logger.error('File does not exist: ' + parsed_args.input)

        # check if output should be interpreted as a filename
        if not parsed_args.many and len(files) == 1:
            output_file = parsed_args.output
        else:
            output_file = None

        if parsed_args.output is not None and output_file is None:
            output_dir = parsed_args.output
            # check if output directory exists
            if output_dir and not os.path.exists(output_dir):
                logger.warning("Directory {:s} does not exist, creating.".format(output_dir))
                os.makedirs(output_dir)
        else:
            output_dir = '.'

        parsed_args.error = ErrorEstimate[parsed_args.error]

        # check required options for tripddd parser
        if parsed_args.command == Converters.tripddd.name and parsed_args.energy is None:
            logger.error("Option --energy is required, provide an energy value")
            return 2
        if parsed_args.command == Converters.tripddd.name and parsed_args.projectile is None:
            logger.error("Option --projectile is required, provide an projectile")
            return 2

        if parsed_args.many:
            status = convertfrompattern(parsed_args.input, output_dir,
                                        converter_name=parsed_args.command, options=parsed_args,
                                        error=parsed_args.error, nan=parsed_args.nan,
                                        jobs=parsed_args.jobs, verbose=parsed_args.verbose)
        else:
            status = convertfromlist(parsed_args.input,
                                     error=parsed_args.error, nan=parsed_args.nan, outputdir=output_dir,
                                     converter_name=parsed_args.command, options=parsed_args, outputfile=output_file)

    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
