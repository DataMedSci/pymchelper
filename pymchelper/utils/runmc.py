#!/usr/bin/env python

import logging
import sys
import argparse

from pymchelper.executor import runner

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
    parser.add_argument('-v',
                        '--verbose',
                        action='count',
                        default=0,
                        help='give more output. Option is additive, and can be used up to 3 times')
    parser.add_argument('-V', '--version', action='version', version=pymchelper.__version__)
    parser.add_argument("input", help='input filename or directory', type=str)
    parser.add_argument('-a', '--args', help='optional arguments for MC engine', type=str, default=None)
    parser.add_argument('-e', '--executable', help='path to executable', type=str, default=None)

    parsed_args = parser.parse_args(args)

    mc_args = parsed_args.args
    if mc_args is not None and len(mc_args) > 1:
        if mc_args[0] == '[' and mc_args[-1] == ']':
            mc_args = mc_args[1:-1]
    s = runner.Executable(parsed_args.input, parsed_args.executable, mc_args)
    s.run()

    print("Output stream:")
    last_communicate = ""
    while s.status != runner.Executable.FAILED_STATUS and s.status != runner.Executable.FINISHED_STATUS:
        if s.communicate != last_communicate:
            last_communicate = s.communicate
            print(last_communicate)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
