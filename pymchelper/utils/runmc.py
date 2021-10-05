#!/usr/bin/env python

import os
import logging
import sys
import argparse
import timeit

from pymchelper.executor.options import SimulationSettings
from pymchelper.executor.runner import OutputDataType, Runner
from pymchelper.writers.plots import PlotDataWriter, ImageWriter


def set_logger_level(args):
    """
    Set logger verbosity and quietness based on parsed arguments
    Checks for presence of quiet (-q) and verbose (-v) switches
    """

    # set default logging level to INFO
    level = "INFO"

    # silence almost all warnings if quite option provided
    # there are two levels:
    #  - normal quiet (-q) with level set to WARNING
    #  - very quiet (-qq)  with level set to ERROR
    #  - very very quiet (-qqq and more)  with level set to CRITICAL
    # quiet option is especially useful when using `runmc` commands in the scripts (i.e. in some loops)
    if args.quiet:
        if args.quiet == 1:
            level = "WARNING"
        if args.quiet == 2:
            level = "ERROR"
        else:
            level = "CRITICAL"
    # verbose option, useful in debugging sets DEBUG level
    elif args.verbose:
        level = "DEBUG"

    logging.basicConfig(level=level)


def main(args=None):
    """
    Entry point to the `runmc` script: argument parsing and calling run method
    """

    if args is None:
        args = sys.argv[1:]
    import pymchelper

    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--executable', help='path to MC executable '
                                                   '(automatically detected if not provided)',
                        type=str, default=None)
    parser.add_argument('-j', '--jobs',
                        help='Number of jobs to run simultaneously (default: {:d})'.format(os.cpu_count()),
                        type=int, default=None)
    parser.add_argument('-m', '--mc-options', help='MC simulation options (default: empty string)',
                        dest='mcopt', type=str, default='')
    parser.add_argument('-o', '--output-dir', help='Output directory (default: .)',
                        dest='outdir', type=str, default='.')
    parser.add_argument('-t', '--out-type', help='output data type (default {:s})'.format(OutputDataType.txt.name),
                        dest='outtype', type=str, nargs='*',
                        choices=[x.name for x in OutputDataType], default=OutputDataType.txt.name)
    parser.add_argument('-w', '--work-dir', help='Workspace directory (default: .)',
                        dest='workspace', type=str, default='.')
    parser.add_argument('-k', '--keep', action='store_true', help='keep workspace directories')
    parser.add_argument('-q', '--quiet', action='count', default=0, help='be silent')
    parser.add_argument('-v',
                        '--verbose',
                        action='count',
                        default=0,
                        help='give more output. Option is additive, and can be used up to 3 times')
    parser.add_argument('-V', '--version', action='version', version=pymchelper.__version__)
    parser.add_argument('input', help='input filename or directory', type=str)

    parsed_args = parser.parse_args(args)

    # set verbose and quietness options
    set_logger_level(parsed_args)

    # strip MC simulation arguments:
    #   we have possibility to pass extra options to MS simulation executable
    #   passing these options in most obvious way, i.e. -m --time 00:15:30 won't work
    #   as argument parsing library will interpret --time as runmc option and not as -m option value
    #   surrounding --time 00:15:30 with "" won't help, as they could be stripped away by shell (i.e. bash)
    #   the only possible way is to embed the MC simulator options with custom wrapping characters, like [,]:
    #      -m "[--time 00:15:30 -v -n 1000]"
    #   here we strip these wrapping characters, if present
    # if no -m option is provided then we need to deal with empty string
    parsed_simulation_opts = parsed_args.mcopt
    # check if list is not None, and if it has at least one element
    if parsed_simulation_opts:
        # check if parsed options are embedded in [,]
        if parsed_simulation_opts[0] == '[' and parsed_simulation_opts[-1] == ']':
            parsed_simulation_opts = parsed_simulation_opts[1:-1]  # strip the list from surrounding brackets

    # set MC simulation settings based on:
    #   - MC simulation input file (i.e. *.inp file for FLUKA) or
    #     directories (i.e. directory with beam.dat, geo.dat etc for SHIELD-HIT12A)
    #   - location of MC simulator executable file (i.e. `shieldhit` or `rfluka`)
    #   - simulation options for the MC engine provided via -m switch (i.e. --time or -v)
    settings = SimulationSettings(input_path=parsed_args.input,
                                  simulator_exec_path=parsed_args.executable,
                                  cmdline_opts=parsed_simulation_opts)

    # create runner object based on MC options and dedicated parallel jobs number
    # note that runner object is only created here, no simulation is started at this point
    # and no directories are being created
    runner_obj = Runner(jobs=parsed_args.jobs,
                        keep_workspace_after_run=parsed_args.keep,
                        output_directory=parsed_args.outdir)

    # start parallel execution of MC simulation
    # temporary directories needed for parallel execution as well as the output are being saved in `outdir`
    # in case of successful execution this would return list of temporary workspaces directories
    # containing partial results from simultaneous parallel executions
    start_time = timeit.default_timer()
    runner_obj.run(settings=settings)
    elapsed = timeit.default_timer() - start_time
    print("MC simulation took {:.3f} seconds".format(elapsed))

    # if simulation was successful proceed to data extraction by combining partial results from simultaneous executions
    # each simulation can produce multiple files
    # results are stored in a dictionary (`data_dict`) with keys being filenames
    # and values being pymchelper `Estimator` objects (which keep i.e. numpy arrays with results)
    data_dict = runner_obj.get_data()

    # if user requests combined results as text files, the code below is used to convert Estimator objects to them
    # note that multiple text files can be created here
    start_time = timeit.default_timer()
    if data_dict and (OutputDataType.txt.name in parsed_args.outtype):
        for core_filename in data_dict:
            logging.debug("Core filename {:s}".format(core_filename))
            output_file = os.path.join(parsed_args.outdir, core_filename)
            writer = PlotDataWriter(output_file, None)
            writer.write(data_dict[core_filename])

    # if user requests combined results as PNG image, the code below is used to convert Estimator objects to them
    # note that multiple PNG files can be created here
    if data_dict and (OutputDataType.plot.name in parsed_args.outtype):
        for core_filename in data_dict:
            output_file = os.path.join(parsed_args.outdir, core_filename)
            writer = ImageWriter(output_file, argparse.Namespace(colormap='gnuplot2', log=''))
            writer.write(data_dict[core_filename])

    elapsed = timeit.default_timer() - start_time
    print("Saving output {:.3f} seconds".format(elapsed))

    runner_obj.clean()

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
