#!/usr/bin/env python

import logging
import sys
import argparse

from pymchelper.executor import runner
from pymchelper.executor.options import MCOptions
from pymchelper.executor.runner import MCOutType
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
                                                   '(automatically discovered if not present)',
                        dest='exec', type=str, default=None)
    parser.add_argument('-j', '--jobs', help='Number of jobs to run simultaneosly (default: 1)',
                        type=int, default=1)
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

    opt = MCOptions()

    print(opt)

    return

    if MCOutType.raw.name not in parsed_args.outtype:
        print("Temp exec")
        s = runner.TempExecutor(parsed_args.input, parsed_args.exec, mc_args)
        results = s.run()
        for item in results:
            print("file", item, "data", results[item])
            if MCOutType.txt.name in parsed_args.outtype:
                writer = PlotDataWriter(item, None)
                writer.write(results[item])
            if MCOutType.plot.name in parsed_args.outtype:
                writer = ImageWriter(item, None)
                writer.write(results[item])
    else:
        s = runner.Executable(parsed_args.input, parsed_args.exec, mc_args)
        s.run()
        print("Output stream:")
        last_communicate = ""
        while s.status != runner.Executable.FAILED_STATUS and s.status != runner.Executable.FINISHED_STATUS:
            if s.communicate != last_communicate:
                last_communicate = s.communicate
                print(last_communicate)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
