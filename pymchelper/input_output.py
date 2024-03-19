import logging
import os
from collections import defaultdict
from glob import glob
from pathlib import Path
from typing import List, Optional

import numpy as np

from pymchelper.averaging import Aggregator, SumAggregator, WeightedStatsAggregator, ConcatenatingAggregator
from pymchelper.estimator import ErrorEstimate, Estimator, average_with_nan
from pymchelper.readers.topas import TopasReaderFactory
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
    reader = None
    fluka_reader = FlukaReaderFactory(filename).get_reader()
    if fluka_reader:
        reader = fluka_reader(filename)
    else:
        sh_reader = SHReaderFactory(filename).get_reader()
        if sh_reader:
            reader = sh_reader(filename)
        else:
            topas_reader = TopasReaderFactory(filename).get_reader()
            if topas_reader:
                reader = topas_reader(filename)
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


def fromfile(filename: str) -> Optional[Estimator]:
    """Read estimator data from a binary file ```filename```"""

    reader = guess_reader(filename)
    if reader is None:
        raise Exception("File format not compatible", filename)
    estimator = Estimator()
    estimator.file_counter = 1
    if not reader.read(estimator):  # some problems occurred during read
        logger.error("Error reading file %s", filename)
        estimator = None
    return estimator


aggregator_type: dict[int, Aggregator] = {
    1: SumAggregator,
    2: WeightedStatsAggregator,
    3: WeightedStatsAggregator,
    4: ConcatenatingAggregator
}


def fromfilelist(input_file_list, error: ErrorEstimate = ErrorEstimate.stderr, nan: bool = True) -> Optional[Estimator]:
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
    elif len(input_file_list) == 1:
        result = fromfile(input_file_list[0])
        if not result:
            return None
    else:
        result = fromfile(input_file_list[0])
        if not result:
            return None

        page_aggregators = []
        for page in result.pages:
            # got a page with "concatenate normalisation"
            current_page_normalisation = getattr(page, 'page_normalized', 2)
            aggregator = aggregator_type[current_page_normalisation]()
            aggregator.update(page.data_raw)
            page_aggregators.append(aggregator)

        for n, filename in enumerate(input_file_list[1:], start=2):
            current_estimator = fromfile(filename)
            for current_page, aggregator in zip(current_estimator.pages, page_aggregators):
                aggregator.update(current_page.data_raw)

        for page, aggregator in zip(result.pages, page_aggregators):
            page.data_raw = aggregator.data
            page.error_raw = aggregator.error()

        # ws_objects = [WeightedStats() for _ in result.pages]
        # for ws, filename in zip(ws_objects, input_file_list):
        #     estimator = fromfile(filename)
        #     if not estimator:
        #         return None
        #     for page_no, page in enumerate(estimator.pages):
        #         ws.update(page.data_raw, estimator.number_of_primaries)
        # for ws, page in zip(ws_objects, result.pages):
        #     page.data_raw = ws.mean
        #     if error != ErrorEstimate.none:
        #         page.error_raw = ws.variance_sample

        # # allocate memory for accumulator in standard deviation calculation
        # # not needed if user requested not to include errors
        # if error != ErrorEstimate.none:
        #     for page in result.pages:
        #         page.error_raw = np.zeros_like(page.data_raw)

        # # loop over all files with n running from 2
        # for n, filename in enumerate(input_file_list[1:], start=2):
        #     current_estimator = fromfile(filename)  # x
        #     logger.info("Reading file %s (%d/%d)", filename, n, len(input_file_list))

        #     if not current_estimator:
        #         logger.warning("File %s could not be read", filename)
        #         return None

        #     result.number_of_primaries += current_estimator.number_of_primaries

        #     for current_page, result_page in zip(current_estimator.pages, result.pages):

        #         # the method `fromfile` gives us pages which are already normalized 'per-primary' (if needed)
        #         # for example dose and fluence are normalized per primary, while count is not

        #         # got a page with "concatenate normalisation"
        #         current_page_normalisation = getattr(current_page, 'page_normalized', None)

        #         # detectors like MATERIAL, RHO do not require averaging, we take them from the first file
        #         if current_page_normalisation == 0:
        #             logger.debug("No averaging, taking first page, instead of %s", current_page.name)
        #         # scorers like COUNT needs to be summed, not averaged
        #         elif current_page_normalisation == 1:
        #             logger.debug("Summing page %s", current_page.name)
        #             result_page.data_raw += current_page.data_raw
        #         # scorers like DOSE, FLUENCE, NORMCOUNT needs to be normalized "per-primary"
        #         elif current_page_normalisation == 2:
        #             logger.debug("Per primary with %s", current_page.name)
        #             # here we get accumulate the "total dose"-like quantities, not the "per-primary"
        #             # later this will be divided by the total number of primaries, from all files
        #             result_page.data_raw += current_page.data_raw * current_estimator.number_of_primaries
        #         # scorers like LET needs to be averaged
        #         elif current_page_normalisation == 3:
        #             logger.debug("Averaging with %s", current_page.name)
        #             # here we accumulate the "LET * primaries" like contributions
        #             # that will be later divided by the total number of primaries, from all files
        #             # so we will get weighted (by number of primaries) average
        #             result_page.data_raw += current_page.data_raw * current_estimator.number_of_primaries
        #         # scorers with sequential data (like phasespace data) needs to be concatenated
        #         elif current_page_normalisation == 4:
        #             logger.debug("Concatenating page %s", current_page.name)
        #             result_page.data_raw = np.concatenate((result_page.data_raw, current_page.data_raw))
        #         # the else-case covers pages for which normalisation flag was not set (i.e. Fluka)
        #         else:
        #             logger.debug("Averaging page %s", current_page.name)
        #             # Running variance algorithm based on algorithm by B. P. Welford,
        #             # presented in Donald Knuth's Art of Computer Programming, Vol 2, page 232, 3rd edition.
        #             # Can be found here: http://www.johndcook.com/blog/standard_deviation/
        #             # and https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Online_algorithm
        #             delta = current_page.data_raw - result_page.data_raw  # delta = x - mean
        #             result_page.data_raw += delta / np.float64(n)
        #             if error != ErrorEstimate.none:
        #                 # the line below is equivalent to M2 += delta * (x - mean)
        #                 result_page.error_raw += delta * (current_page.data_raw - result_page.data_raw)

        # # averaged or normalized quantities needs to be divided by the total number of primaries
        # if len(input_file_list) > 1:
        #     for page in result.pages:
        #         if page.page_normalized in {2, 3}:
        #             page.data_raw /= result.number_of_primaries

        # # # unbiased sample variance is stored in `__M2 / (n - 1)`
        # # # unbiased sample standard deviation in classical algorithm is calculated as (sqrt(1/(n-1)sum(x-<x>)**2)
        # # # here it is calculated as square root of unbiased sample variance:
        # # if len(input_file_list) > 1 and error != ErrorEstimate.none:
        # #     for page in result.pages:
        # #         page.error_raw = np.sqrt(page.error_raw / (len(input_file_list) - 1.0))

        # # # if user requested standard error then we calculate it as:
        # # # S = stderr = stddev / sqrt(N), or in other words,
        # # # S = s/sqrt(N) where S is the corrected standard deviation of the mean.
        # # if len(input_file_list) > 1 and error == ErrorEstimate.stderr:
        # #     for page in result.pages:
        # #         page.error_raw /= np.sqrt(len(input_file_list))  # np.sqrt() always returns np.float64

    result.file_counter = len(input_file_list)
    core_names_dict = group_input_files(input_file_list)
    if len(core_names_dict) == 1:
        result.file_corename = list(core_names_dict)[0]

    return result


def frompattern(pattern: str, error: ErrorEstimate = ErrorEstimate.stderr, nan: bool = True):
    """
    Reads all files matching pattern, e.g.: 'foobar_*.bdo', and returns a list of averaged estimators.

    :param pattern: pattern to be matched for reading.
    :param error: error estimation, see class ErrorEstimate class in pymchelper.estimator
    :param nan: if True, NaN (not a number) are excluded when averaging data.
    :return: a list of estimators, or an empty list if no files were found.
    """

    try:
        list_of_matching_files = glob(pattern)
    except TypeError as e:  # noqa: F841
        list_of_matching_files = pattern

    core_names_dict = group_input_files(list_of_matching_files)

    result = [fromfilelist(filelist, error, nan) for _, filelist in core_names_dict.items()]

    return result


def get_topas_estimators(output_files_path: str) -> List[Estimator]:
    """Get Topas estimators from provided directory"""
    estimators_list = []
    for path in Path(output_files_path).iterdir():
        topas_reader = TopasReaderFactory(str(path)).get_reader()
        if topas_reader:
            reader = topas_reader(path)
            estimator = Estimator()
            reader.read(estimator)
            estimators_list.append(estimator)

    return estimators_list


def convertfromlist(filelist, error, nan, outputdir, converter_name, options, outputfile=None):
    """
    :param filelist:
    :param error: error estimation, see class ErrorEstimate class in pymchelper.estimator
    :param nan: if True, NaN (not a number) are excluded when averaging data.
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


def convertfrompattern(pattern, outputdir, converter_name, options, error=ErrorEstimate.stderr, nan: bool = True):
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
