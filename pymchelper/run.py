#!/usr/bin/env python

import argparse
import glob
import logging
import sys

from pymchelper.estimator import ErrorEstimate
from pymchelper.input_output import convertfromlist, convertfrompattern
from pymchelper.writers.common import Converters
from pymchelper.writers.plots import ImageWriter, PlotAxis

logger = logging.getLogger(__name__)


def add_default_options(parser):
    import pymchelper
    parser.add_argument('input', help='input filename, file list or pattern', type=str)
    parser.add_argument('output', help='output filename or directory', nargs='?')
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


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import os

    import pymchelper

    _progname = os.path.basename(sys.argv[0])
    _helptxt = 'Universal converter for FLUKA and SHIELD-HIT12A output files.'
    _epitxt = f"Type '{_progname} <converter> --help' for help on a specific converter."

    parser = argparse.ArgumentParser(description=_helptxt, epilog=_epitxt)

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
                              help='image color map, see https://matplotlib.org/stable/tutorials/colors/colormaps.html '
                                   'for list of possible options (default: ' + ImageWriter.default_colormap + ')',
                              default=ImageWriter.default_colormap,
                              type=str)

    parser_excel = subparsers.add_parser(Converters.excel.name, help='converts to MS Excel file')
    add_default_options(parser_excel)

    parser_hdf = subparsers.add_parser(Converters.hdf.name, help='converts to HDF file')
    add_default_options(parser_hdf)

    parser_plotdata = subparsers.add_parser(Converters.plotdata.name, help='converts to plot data')
    add_default_options(parser_plotdata)

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

    parser_tripcube = subparsers.add_parser(Converters.tripcube.name, help='converts to TRiP98 data cube')
    add_default_options(parser_tripcube)

    parser_tripddd = subparsers.add_parser(Converters.tripddd.name, help='converts to TRiP98 DDD file')
    add_default_options(parser_tripddd)
    parser_tripddd.add_argument("--energy",
                                help='energy of the beam [MeV/amu] (guess from data if option missing)',
                                type=float)
    parser_tripddd.add_argument("--projectile",
                                help='projectile (guess from data if option missing)',
                                type=str)
    parser_tripddd.add_argument("--ngauss",
                                help='number of Gaussian functions to fit (default: 0)',
                                choices=(0, 1, 2),
                                default=0,
                                type=int)

    parser.add_argument('-V', '--version', action='version', version=pymchelper.__version__)

    parsed_args = parser.parse_args(args)

    verbose_flag = getattr(parsed_args, 'verbose', 0)
    if verbose_flag == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbose_flag > 1:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()

    status = 0
    if parsed_args.command is not None:
        # TODO add filename discovery
        files = sorted(glob.glob(parsed_args.input))
        if not files:
            logger.error(f'File {parsed_args.input} does not exist: ')

        # check if output should be interpreted as a filename
        if not parsed_args.many and len(files) == 1:
            output_file = parsed_args.output
        else:
            output_file = None

        if parsed_args.output is not None and output_file is None:
            output_dir = parsed_args.output
            # check if output directory exists
            if output_dir and not os.path.exists(output_dir):
                logger.warning(f"Directory {output_dir} does not exist, creating.")
                os.makedirs(output_dir)
        else:
            output_dir = '.'

        parsed_args.error = ErrorEstimate[parsed_args.error]

        if parsed_args.many:
            status = convertfrompattern(parsed_args.input, output_dir,
                                        converter_name=parsed_args.command, options=parsed_args,
                                        error=parsed_args.error, nan=parsed_args.nan)
        else:
            status = convertfromlist(parsed_args.input,
                                     error=parsed_args.error, nan=parsed_args.nan, outputdir=output_dir,
                                     converter_name=parsed_args.command, options=parsed_args, outputfile=output_file)

    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
