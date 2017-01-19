#!/usr/bin/env python

import os
import logging
import sys
import argparse

from pymchelper.executor.options import MCOptions
from pymchelper.executor.runner import MCOutType, Runner
from pymchelper.writers.plots import PlotDataWriter, ImageWriter

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
    parser.add_argument('-e', '--executable', help='path to MC executable '
                                                   '(automatically detected if option not present)',
                        type=str, default=None)
    parser.add_argument('-j', '--jobs',
                        help='Number of jobs to run simultaneously (default: {:d})'.format(os.cpu_count()),
                        type=int, default=None)
    parser.add_argument('-m', '--mc-options', help='MC engine options (default: none)',
                        dest='mcopt', type=str, default=None)
    parser.add_argument('-o', '--output-dir', help='Output directory (default: .)',
                        dest='outdir', type=str, default='.')
    parser.add_argument('-t', '--out-type', help='output data type (default {:s})'.format(MCOutType.txt.name),
                        dest='outtype', type=str,
                        choices=[x.name for x in MCOutType], default=MCOutType.txt.name)
    parser.add_argument('-w', '--work-dir', help='Workspace directory (default: .)',
                        dest='workspace', type=str, default='.')
    parser.add_argument('-v',
                        '--verbose',
                        action='count',
                        default=0,
                        help='give more output. Option is additive, and can be used up to 3 times')
    parser.add_argument('-V', '--version', action='version', version=pymchelper.__version__)
    parser.add_argument('input', help='input filename or directory', type=str)

    parsed_args = parser.parse_args(args)

    # strip MC arguments
    mc_args = parsed_args.mcopt
    if mc_args is not None and len(mc_args) > 1:
        if mc_args[0] == '[' and mc_args[-1] == ']':
            mc_args = mc_args[1:-1]

    opt = MCOptions(input_cfg=parsed_args.input,
                    executable_path=parsed_args.executable,
                    user_opt=mc_args)

    r = Runner(jobs=parsed_args.jobs, options=opt)
    workspaces = r.run(outdir=parsed_args.outdir)
    data = r.get_data(workspaces)
    print(data)

    if MCOutType.txt.name in parsed_args.outtype:
        for key in data:
            output_file = os.path.join(parsed_args.outdir, key)
            writer = PlotDataWriter(output_file, None)
            writer.write(data[key])

    if MCOutType.plot.name in parsed_args.outtype:
        for key in data:
            output_file = os.path.join(parsed_args.outdir, key)
            writer = ImageWriter(output_file, argparse.Namespace(colormap='gnuplot2'))
            writer.write(data[key])

    if MCOutType.raw.name not in parsed_args.outtype:
        r.clean(workspaces)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
