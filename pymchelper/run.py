#!/usr/bin/env python

import glob
import logging
import sys

import argparse

from pymchelper.detector import merge_list, merge_many, SHConverters
from pymchelper.writers.plots import SHImageWriter

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


def main(args=sys.argv[1:]):
    import pymchelper
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v',
        '--verbose',
        action='count',
        default=0,
        help='Give more output. Option is additive, and can be used up to 3 times')
    parser.add_argument('-q', '--quiet', action='count', default=0, help='Be silent')
    parser.add_argument("inputfile", help='input filename, file list or pattern', type=str)
    parser.add_argument("outputfile", help='output filename', nargs='?')
    parser.add_argument("--many", help='automatically merge data from various sources', action="store_true")
    parser.add_argument("--nan", help='ignore NaN in averaging', action="store_true")
    parser.add_argument(
        "--converter",
        help='converters',
        default=(SHConverters.standard.name,),
        choices=[x.name for x in SHConverters],
        nargs='+')
    parser.add_argument("--colormap", help='image color map', default=SHImageWriter.default_colormap, type=str)
    parser.add_argument('-V', '--version', action='version', version=pymchelper.__version__)
    parsed_args = parser.parse_args(args)

    set_logger_level(parsed_args)

    # TODO add filename discovery

    files = sorted(glob.glob(parsed_args.inputfile))
    if not files:
        logger.error('File does not exist: ' + parsed_args.inputfile)

    if parsed_args.outputfile is None:
        parsed_args.outputfile = files[0][:-3] + "txt"

    if parsed_args.many:
        merge_many(files, parsed_args.converter, parsed_args.nan, parsed_args.colormap)
    else:
        merge_list(files, parsed_args.outputfile, parsed_args.converter, parsed_args.nan, parsed_args.colormap)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
