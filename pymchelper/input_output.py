from enum import IntEnum
import logging
import gc
import os
from collections import defaultdict
from glob import glob
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

import numpy as np

from pymchelper.averaging import (Aggregator, SumAggregator, WeightedStatsAggregator, ConcatenatingAggregator,
                                  NoAggregator)
from pymchelper.estimator import ErrorEstimate, Estimator, average_with_nan
from pymchelper.readers.topas import TopasReaderFactory
from pymchelper.readers.fluka import FlukaReader, FlukaReaderFactory
from pymchelper.readers.shieldhit.general import SHReaderFactory
from pymchelper.readers.shieldhit.reader_base import SHReader
from pymchelper.writers.common import Converters

logger = logging.getLogger(__name__)


class AggregationType(IntEnum):
    """
    Enum for different types of aggregation.
    This enum is related to integer value stored in SHIELD-HIT12A binary files,
    which defines how the data is aggregated.
    Below few examples of how such aggregation is used in SHIELD-HIT12A:

      - NoAggregation is used for density (RHO) and material scorer.
      - Sum is used for particle counter (COUNT).
      - AveragingCumulative is used for dose and fluence scorers.
      - AveragingPerPrimary is used for LET scorers (TLET and DLET).
      - Concatenation is used for phase space (MCPL) scorer.
    """

    NoAggregation = 0
    Sum = 1
    AveragingCumulative = 2
    AveragingPerPrimary = 3
    Concatenation = 4


def guess_reader(filename: str) -> Optional[object]:
    """
    Guess a reader based on file contents or extensions.
    In some cases (i.e. binary SHIELD-HIT12A files) access to file contents is needed.
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


def guess_corename(filename: str) -> str:
    """
    Guess a reader based on file contents or extensions.
    In some cases (i.e. binary SHIELD-HIT12A files) access to file contents is needed.
    :param filename:
    :return: the corename of the file (i.e. the basename without the running number for averaging)
    """
    corename = FlukaReader(filename).corename
    if corename is None:
        corename = SHReader(filename).corename
    return corename


def fromfile(filename: str) -> Optional[Estimator]:
    """
    Read estimator data from a binary file `filename`
    Note that for the in some cases the data are post-processes (i.e. normalized) after reading.
    For example SHIELD-HIT12A saves dose and fluence data as cumulative values,
    which are normalized by the number of primaries after by the Reader responsible for parsing binary files.
    This way dose and fluence (and other similar quantities) are saved in Estimator as "per primary" values.
    Fluka on the other hand saves dose and fluence as "per primary" values, so no normalization is needed.
    """

    reader = guess_reader(filename)
    if reader is None:
        raise Exception("File format not compatible", filename)
    estimator = Estimator()
    estimator.file_counter = 1
    if not reader.read(estimator):  # some problems occurred during read
        logger.error("Error reading file %s", filename)
        return None
    return estimator


def fromfilelist(input_file_list: Union[List[str], str],
                 error: ErrorEstimate = ErrorEstimate.stderr,
                 nan: bool = False) -> Optional[Estimator]:
    """
    Reads all files from a given list using `fromfile` method, and returns a list of averaged estimators.

    :param input_file_list: list of files to be read
    :param error: error estimation, see class ErrorEstimate class in pymchelper.estimator
    :param nan: if True, NaN (not a number) are excluded when averaging data.
    :return: list of estimators, or None if any of the files could not be read
    """
    if not isinstance(input_file_list, list):  # probably a string instead of list
        input_file_list = [input_file_list]

    result: Optional[Estimator]
    if nan:
        estimator_list = []
        for filename in input_file_list:
            estimator = fromfile(filename)
            if estimator is None:
                return None
            estimator_list.append(estimator)
        result = average_with_nan(estimator_list, error)
    else:
        result = _aggregate_files(input_file_list, error)
    if result is None:
        return None

    result.file_counter = len(input_file_list)
    core_names_dict = group_input_files(input_file_list)
    if len(core_names_dict) == 1:
        result.file_corename = list(core_names_dict)[0]

    return result


def _aggregate_files(input_file_list: List[str], error: ErrorEstimate) -> Optional[Estimator]:
    """
    Reads the files one by one and aggregates their pages, see `pymchelper.averaging`.

    :return: estimator with aggregated data, or None if any of the files could not be read
    """
    result = fromfile(input_file_list[0])
    if result is None or len(input_file_list) == 1:
        return result

    # _aggregator_mapping maps SHIELD-HIT12A normalization types (integers) to pymchelper aggregators
    # using enums for clarity. AveragingCumulative (e.g., dose) and AveragingPerPrimary (e.g., LET)
    # both utilize WeightedStatsAggregator. SHIELD-HIT12A stores "cumulative-like" data (e.g., dose,
    # fluence) in BDO format as quantities for all particles. pymchelper normalizes this upon reading
    # a BDO file by the number of primaries, making the `estimator` object data pre-normalized. Hence,
    # aggregation for "cumulative-like" and "per-primary" data is handled uniformly in this mapping.
    # keys are plain integers (AggregationType is an IntEnum), as read from the binary files
    _aggregator_mapping: Dict[int, Type[Aggregator]] = {
        AggregationType.NoAggregation: NoAggregator,
        AggregationType.Sum: SumAggregator,
        AggregationType.AveragingCumulative: WeightedStatsAggregator,
        AggregationType.AveragingPerPrimary: WeightedStatsAggregator,
        AggregationType.Concatenation: ConcatenatingAggregator
    }

    # create aggregators for each page and fill them with data from first file
    page_aggregators = []
    for page in result.pages:

        # if no normalization attribute present (Fluka?) we can assume it is a cumulative-like quantity
        current_page_normalisation = getattr(page, 'page_normalized', AggregationType.AveragingCumulative.value)

        # guess the aggregator based on the normalisation type
        aggregator = _aggregator_mapping.get(current_page_normalisation, WeightedStatsAggregator)()
        logger.debug("Selected aggregator %s for page %s", aggregator, page.name)

        # feed the aggregator with data from the first file
        aggregator.update(value=page.data_raw, weight=result.number_of_primaries)
        page_aggregators.append(aggregator)

    # process all other files, if there are any
    for filename in input_file_list[1:]:
        current_estimator = fromfile(filename)
        if current_estimator is None:
            return None
        for current_page, aggregator in zip(current_estimator.pages, page_aggregators):
            aggregator.update(value=current_page.data_raw, weight=current_estimator.number_of_primaries)

        # force garbage collection if the estimator is too large
        estimator_size_mbytes = sum(page.data_raw.nbytes for page in current_estimator.pages) / 1024 / 1024
        gc_threshold_mbytes = 100
        if estimator_size_mbytes > gc_threshold_mbytes:
            logger.info("Large estimator (%.1f MB) detected, performing garbage collection", estimator_size_mbytes)
            gc.collect()
        result.number_of_primaries += current_estimator.number_of_primaries

    # extract data from aggregators and fill then into the result
    for page, aggregator in zip(result.pages, page_aggregators):
        logger.debug("Extracting data from aggregator %s for page %s", aggregator, page.name)
        page.data_raw = np.asarray(aggregator.data)
        page_error = aggregator.error(error_type=error.name)
        # only WeightedStatsAggregator estimates the error, other aggregators and ErrorEstimate.none give None,
        # which means the page has no error data
        if page_error is None:
            page.error_raw = None
        else:
            # the error may come as a plain float, while error_raw holds an array
            page.error_raw = np.asarray(page_error)

    return result


def frompattern(pattern: Union[str, List[str]],
                error: ErrorEstimate = ErrorEstimate.stderr,
                nan: bool = True) -> List[Optional[Estimator]]:
    """
    Reads all files matching pattern, e.g.: 'foobar_*.bdo', and returns a list of averaged estimators.

    :param pattern: pattern to be matched for reading, or a list of files to read.
    :param error: error estimation, see class ErrorEstimate class in pymchelper.estimator
    :param nan: if True, NaN (not a number) are excluded when averaging data.
    :return: a list of estimators, or an empty list if no files were found.
    """

    if isinstance(pattern, str):
        list_of_matching_files = sorted(glob(pattern))
    else:
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


def convertfromlist(filelist: List[str],
                    error: ErrorEstimate,
                    nan: bool,
                    outputdir: Optional[str],
                    converter_name: str,
                    options: object,
                    outputfile: Optional[str] = None) -> Optional[int]:
    """Convert a list of input files into a single output using a chosen converter.

    - Reads and optionally averages inputs (`nan` controls NaN handling).
    - Resolves output path (`outputfile` overrides, else uses `outputdir` or corename).
    - Writes via `converter_name` with `options`.

    Returns status code from the writer, or None if reading failed.
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


def convertfrompattern(pattern: str,
                       outputdir: Optional[str],
                       converter_name: str,
                       options: object,
                       error: ErrorEstimate = ErrorEstimate.stderr,
                       nan: bool = True) -> int:
    """Convert all files matching a glob `pattern` using the chosen converter.

    - Groups matching files by corename and processes each group via `convertfromlist`.
    - Supports NaN-aware averaging (`nan`) and error type selection (`error`).

    Returns the maximum status code across processed groups, 1 if no file matches or a group could not be read.
    """
    list_of_matching_files = sorted(glob(pattern))
    if not list_of_matching_files:
        logger.error("No files matching %s", pattern)
        return 1

    core_names_dict = group_input_files(list_of_matching_files)

    status = []
    for _, filelist in core_names_dict.items():
        group_status = convertfromlist(filelist, error, nan, outputdir, converter_name, options)
        # convertfromlist gives None when files of the group could not be read, count it as a failure
        if group_status is None:
            status.append(1)
        else:
            status.append(group_status)
    return max(status)


def tofile(estimator: Estimator, filename: str, converter_name: str, options: object) -> int:
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


def group_input_files(input_file_list: List[str]) -> Dict[str, List[str]]:
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
