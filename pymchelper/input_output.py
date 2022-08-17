import logging
import os
from collections import defaultdict
from glob import glob

import numpy as np

from pymchelper.estimator import ErrorEstimate, Estimator, average_with_nan
from pymchelper.readers.fluka import FlukaReader, FlukaReaderFactory
from pymchelper.readers.shieldhit.general import SHReaderFactory
from pymchelper.readers.shieldhit.reader_base import SHReader
from pymchelper.writers.common import Converters

logger = logging.getLogger(__name__)


def guess_reader(filename):
    """
    Guess a reader based on file contents or extensions.
    In some cases (i.e. binary SH12A files) access to file contents is needed.
    :param filename:
    :return: Instantiated reader object
    """
    fluka_reader = FlukaReaderFactory(filename).get_reader()
    if fluka_reader:
        reader = fluka_reader(filename)
    else:
        sh_reader = SHReaderFactory(filename).get_reader()
        if sh_reader:
            reader = sh_reader(filename)
    return reader


def guess_corename(filename):
    """
    Guess a reader based on file contents or extensions.
    In some cases (i.e. binary SH12A files) access to file contents is needed.
    :param filename:
    :return: the corename of the file (i.e. the basename without the running number for averaging)
    """
    corename = FlukaReader(filename).corename
    if corename is None:
        corename = SHReader(filename).corename
    return corename


def fromfile(filename):
    """Read estimator data from a binary file ```filename```"""

    reader = guess_reader(filename)
    if reader is None:
        raise Exception("File format not compatible", filename)
    estimator = Estimator()
    estimator.file_counter = 1
    if not reader.read(estimator):  # some problems occurred during read
        estimator = None
    return estimator


def fromfilelist(input_file_list, error=ErrorEstimate.stderr, nan: bool = True):
    """
    Reads all files from a given list, and returns a list of averaged estimators.

    :param input_file_list: list of files to be read
    :param error: error estimation, see class ErrorEstimate class in pymchelper.estimator
    :param nan: if True, NaN (not a number) are excluded when averaging data.
    :return: list of estimators
    """
    if not isinstance(input_file_list, list):  # probably a string instead of list
        input_file_list = [input_file_list]

    if nan:
        estimator_list = [fromfile(filename) for filename in input_file_list]
        result = average_with_nan(estimator_list, error)
        if not result:  # TODO check here !
            return None
    elif len(input_file_list) == 1:
        result = fromfile(input_file_list[0])
        if not result:
            return None
    else:
        result = fromfile(input_file_list[0])
        if not result:
            return None

        # allocate memory for accumulator in standard deviation calculation
        # not needed if user requested not to include errors
        if error != ErrorEstimate.none:
            for page in result.pages:
                page.error_raw = np.zeros_like(page.data_raw)

        # loop over all files with n running from 2
        for n, filename in enumerate(input_file_list[1:], start=2):
            current_estimator = fromfile(filename)  # x

            # Running variance algorithm based on algorithm by B. P. Welford,
            # presented in Donald Knuth's Art of Computer Programming, Vol 2, page 232, 3rd edition.
            # Can be found here: http://www.johndcook.com/blog/standard_deviation/
            # and https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Online_algorithm
            delta = [
                current_page.data_raw - result_page.data_raw
                for current_page, result_page in zip(current_estimator.pages, result.pages)
            ]  # delta = x - mean
            for page, delta_item in zip(result.pages, delta):
                page.data_raw += delta_item / np.float64(n)

            if error != ErrorEstimate.none:
                for page, delta_item, current_page in zip(result.pages, delta, current_estimator.pages):
                    page.error_raw += delta_item * (current_page.data_raw - page.data_raw)  # M2 += delta * (x - mean)

        # unbiased sample variance is stored in `__M2 / (n - 1)`
        # unbiased sample standard deviation in classical algorithm is calculated as (sqrt(1/(n-1)sum(x-<x>)**2)
        # here it is calculated as square root of unbiased sample variance:
        if len(input_file_list) > 1 and error != ErrorEstimate.none:
            for page in result.pages:
                page.error_raw = np.sqrt(page.error_raw / (len(input_file_list) - 1.0))

        # if user requested standard error then we calculate it as:
        # S = stderr = stddev / sqrt(N), or in other words,
        # S = s/sqrt(N) where S is the corrected standard deviation of the mean.
        if len(input_file_list) > 1 and error == ErrorEstimate.stderr:
            for page in result.pages:
                page.error_raw /= np.sqrt(len(input_file_list))  # np.sqrt() always returns np.float64

    result.file_counter = len(input_file_list)
    core_names_dict = group_input_files(input_file_list)
    if len(core_names_dict) == 1:
        result.file_corename = list(core_names_dict)[0]

    return result


def frompattern(pattern, error=ErrorEstimate.stderr, nan=True):
    """
    Reads all files matching pattern, e.g.: 'foobar_*.bdo', and returns a list of averaged estimators.

    :param pattern: pattern to be matched for reading.
    :param error: error estimation, see class ErrorEstimate class in pymchelper.estimator
    :param nan: if True, NaN (not a number) are excluded when averaing data.
    :return: a list of estimators, or an empty list if no files were found.
    """

    try:
        list_of_matching_files = glob(pattern)
    except TypeError as e:  # noqa: F841
        list_of_matching_files = pattern

    core_names_dict = group_input_files(list_of_matching_files)

    result = [fromfilelist(filelist, error, nan) for _, filelist in core_names_dict.items()]
    return result


def convertfromlist(filelist, error, nan, outputdir, converter_name, options, outputfile=None):
    """

    :param filelist:
    :param error: error estimation, see class ErrorEstimate class in pymchelper.estimator
    :param nan: if True, NaN (not a number) are excluded when averaing data.
    :param outputdir:
    :param converter_name:
    :param options:
    :param outputfile:
    :return:
    """
    estimator = fromfilelist(filelist, error, nan)
    if not estimator:
        return None
    if outputfile is not None:
        output_path = outputfile
    elif outputdir is None:
        output_path = estimator.file_corename
    else:
        output_path = os.path.join(outputdir, estimator.file_corename)
    status = tofile(estimator, output_path, converter_name, options)
    return status


def convertfrompattern(pattern,
                       outputdir,
                       converter_name,
                       options,
                       error=ErrorEstimate.stderr,
                       nan: bool = True):
    """

    :param pattern:
    :param outputdir:
    :param converter_name:
    :param options:
    :param error: error estimation, see class ErrorEstimate class in pymchelper.estimator
    :param nan: if True, NaN (not a number) are excluded when averaging data.
    :return:
    """
    list_of_matching_files = glob(pattern)

    core_names_dict = group_input_files(list_of_matching_files)

    status = []
    for _, filelist in core_names_dict.items():
        status.append(convertfromlist(filelist, error, nan, outputdir, converter_name, options))
    return max(status)


def tofile(estimator, filename, converter_name, options):
    """
    Save a estimator data to a ``filename`` using converter defined by ``converter_name``
    :param estimator:
    :param filename:
    :param converter_name:
    :param options:
    :return:
    """
    writer_cls = Converters.fromname(converter_name)
    writer = writer_cls(filename, options)
    logger.debug(f"File corename : {filename}")
    status = writer.write(estimator)
    return status


def group_input_files(input_file_list):
    """
    Takes set of input file names, belonging to possibly different estimators.
    Input files are grouped according to the estimators and for each group
    merging is performed, as in @merge_list method.
    Output file name is automatically generated.
    :param input_file_list: list of input files
    :return: core_names_dict
    """
    core_names_dict = defaultdict(list)
    # keys - core_name, value - list of full paths to corresponding files

    # loop over input list of file paths
    for filepath in input_file_list:
        core_name = guess_corename(filepath)
        core_names_dict[core_name].append(filepath)

    return core_names_dict
