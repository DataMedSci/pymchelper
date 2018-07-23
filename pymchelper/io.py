from glob import glob
import logging
import os

import numpy as np

from pymchelper.detector import Detector, average_with_nan, ErrorEstimate
from pymchelper.readers.common import guess_reader, group_input_files
from pymchelper.writers.common import Converters

logger = logging.getLogger(__name__)


def fromfile(filename):
    """Read a detector data from a binary file ```filename```"""

    reader = guess_reader(filename)
    detector = Detector()
    detector.counter = 1
    reader.read(detector)
    detector.error_raw = np.zeros_like(detector.data_raw)
    detector.error_raw *= np.nan
    return detector


def fromfilelist(input_file_list, error, nan):
    """

    :param input_file_list:
    :param error:
    :param nan:
    :return:
    """
    if not isinstance(input_file_list, list):  # probably a string instead of list
        input_file_list = [input_file_list]

    if nan:
        detector_list = [fromfile(filename) for filename in input_file_list]
        result = average_with_nan(detector_list, error)
    elif len(input_file_list) == 1:
        result = fromfile(input_file_list[0])
    else:
        result = fromfile(input_file_list[0])

        # allocate memory for accumulator in standard deviation calculation
        # not needed if user requested not to include errors
        if error != ErrorEstimate.none:
            m2 = np.zeros_like(result.data_raw)

        # loop over all files
        for n, filename in enumerate(input_file_list[1:], start=2):
            x = fromfile(filename).data_raw

            # Running variance algorithm based on algorithm by B. P. Welford,
            # presented in Donald Knuth's Art of Computer Programming, Vol 2, page 232, 3rd edition.
            # Can be found here: http://www.johndcook.com/blog/standard_deviation/
            # and https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Online_algorithm
            delta = x - result.data_raw               # delta = x - mean
            result.data_raw += delta / n              # mean += delta / n
            if error != ErrorEstimate.none:
                m2 += delta * (x - result.data_raw)   # M2 += delta * (x - mean)

        # unbiased sample variance is stored in `__M2 / (n - 1)`
        # unbiased sample standard deviation in classical algorithm is calculated as (sqrt(1/(n-1)sum(x-<x>)**2)
        # here it is calculated as square root of unbiased sample variance:
        if len(input_file_list) > 1 and error != ErrorEstimate.none:
            result.error_raw = np.sqrt(m2 / (len(input_file_list) - 1))

        # if user requested standard error then we calculate it as:
        # S = stderr = stddev / sqrt(N), or in other words,
        # S = s/sqrt(N) where S is the corrected standard deviation of the mean.
        if len(input_file_list) > 1 and error == ErrorEstimate.stderr:
            result.error_raw /= np.sqrt(len(input_file_list))  # np.sqrt() always returns np.float64

    result.counter = len(input_file_list)
    core_names_dict = group_input_files(input_file_list)
    if len(core_names_dict) == 1:
        result.corename = list(core_names_dict)[0]

    return result


def frompattern(pattern, error, nan, jobs=-1, verbose=0):
    """

    :param pattern:
    :param error:
    :param nan:
    :param jobs:
    :param verbose:
    :return:
    """
    list_of_matching_files = glob(pattern)

    core_names_dict = group_input_files(list_of_matching_files)

    # parallel execution of output file generation, using all CPU cores
    # see http://pythonhosted.org/joblib
    try:
        from joblib import Parallel, delayed
        logger.info("Parallel processing on {:d} jobs (-1 means all)".format(jobs))
        # options.verbose count the number of `-v` switches provided by user
        # joblib Parallel class expects the verbosity as a larger number (i.e. multiple of 10)
        worker = Parallel(n_jobs=jobs, verbose=verbose * 10)
        result = worker(
            delayed(fromfilelist)(filelist, error, nan)
            for core_name, filelist in core_names_dict.items()
        )
    except (ImportError, SyntaxError):
        # single-cpu implementation, in case joblib library fails (i.e. Python 3.2)
        logger.info("Single CPU processing")
        result = [fromfilelist(filelist, error, nan)
                  for core_name, filelist in core_names_dict.items()]
    return result


def convertfromlist(filelist, error, nan, outputdir, converter_name, options, outputfile=None):
    """

    :param filelist:
    :param error:
    :param nan:
    :param outputdir:
    :param converter_name:
    :param options:
    :param outputfile:
    :return:
    """
    detector = fromfilelist(filelist, error, nan)
    if outputfile is not None:
        output_path = outputfile
    elif outputdir is None:
        output_path = detector.corename
    else:
        output_path = os.path.join(outputdir, detector.corename)
    status = tofile(detector, output_path, converter_name, options)
    return status


def convertfrompattern(pattern, outputdir, converter_name, options,
                       error=ErrorEstimate.stderr, nan=True, jobs=-1, verbose=0):
    """

    :param pattern:
    :param outputdir:
    :param converter_name:
    :param options:
    :param error:
    :param nan:
    :param jobs:
    :param verbose:
    :return:
    """
    list_of_matching_files = glob(pattern)

    core_names_dict = group_input_files(list_of_matching_files)

    # parallel execution of output file generation, using all CPU cores
    # see http://pythonhosted.org/joblib
    try:
        from joblib import Parallel, delayed
        logger.info("Parallel processing on {:d} jobs (-1 means all)".format(jobs))
        # options.verbose count the number of `-v` switches provided by user
        # joblib Parallel class expects the verbosity as a larger number (i.e. multiple of 10)
        worker = Parallel(n_jobs=jobs, verbose=verbose * 10)
        status = worker(
            delayed(convertfromlist)(filelist, error, nan, outputdir, converter_name, options)
            for core_name, filelist in core_names_dict.items()
        )
        return max(status)
    except (ImportError, SyntaxError):
        # single-cpu implementation, in case joblib library fails (i.e. Python 3.2)
        logger.info("Single CPU processing")
        status = []
        for core_name, filelist in core_names_dict.items():
            status.append(convertfromlist(filelist, error, nan, outputdir, converter_name, options))
        return max(status)


def tofile(detector, filename, converter_name, options):
    """
    Save a detector data to a ``filename`` using converter defined by ``converter_name``
    :param detector:
    :param filename:
    :param converter_name:
    :param options:
    :return:
    """
    writer_cls = Converters.fromname(converter_name)
    writer = writer_cls(filename, options)
    logger.debug("Writing file with corename {:s}".format(filename))
    status = writer.write(detector)
    return status
