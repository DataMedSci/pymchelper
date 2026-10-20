import copy
from enum import IntEnum
import logging
from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy as np
from pymchelper.shieldhit.detector.estimator_type import SHGeoType

if TYPE_CHECKING:
    from pymchelper.page import Page

logger = logging.getLogger(__name__)


class ErrorEstimate(IntEnum):
    """
    When averaging data multiple files we could estimate statistical error of scored quantity.
    Such error can be calculated as: none (error information missing), standard error or standard deviation.
    """
    none = 0
    stderr = 1
    stddev = 2


class Estimator:
    """
    Estimator data read from one or more files of the same MC output.

    This class handles in universal way data generated with MC code.
    Scored data and the scoring mesh are kept in pages (see ``Page`` class), one page per scored quantity.
    Several other fields are also used:
    - nstat: number of simulated histories
    - counter: number of files read to construct detector object
    - corename: common core part of input files defining a name of detector
    - error_type: none, stderr or stddev - error type

    Estimator data can be either read from the file (see ``fromfile`` method in ``input_output`` module
    or constructed directly:

    >>> e = Estimator()
    """

    def __init__(self) -> None:
        """
        Create dummy estimator object.
        >>> e = Estimator()
        """
        self.number_of_primaries = 0  # number of histories simulated
        self.file_counter = 0  # number of files read
        self.file_corename = ""  # common core for paths of contributing files
        self.file_format = ""  # binary file format of the input files
        self.data_order = 'F'  # memory order of data array: 'F' (Fortran/column-major) or 'C' (C/row-major)
        self.error_type = ErrorEstimate.none
        self.geotyp: Optional[SHGeoType] = None  # MSH, CYL, etc...

        self.pages: Tuple['Page', ...] = ()  # empty tuple of pages at the beginning

    def add_page(self, page: 'Page') -> None:
        """
        Add a page to the estimator object.
        New copy of page is made and page estimator pointer is set to the estimator object holding this page.
        :param page:
        :return: None
        """
        new_page = copy.deepcopy(page)
        new_page.estimator = self
        self.pages += (new_page, )


def average_with_nan(estimator_list: List[Estimator],
                     error_estimate: ErrorEstimate = ErrorEstimate.stderr) -> Optional[Estimator]:
    """
    Calculate average estimator object, excluding malformed data (NaN) from averaging.
    :param estimator_list:
    :param error_estimate:
    :return:
    """
    # TODO add compatibility check
    if not estimator_list:
        return None
    result = copy.deepcopy(estimator_list[0])
    result.number_of_primaries = sum(estimator.number_of_primaries for estimator in estimator_list)
    for page_no, page in enumerate(result.pages):
        page.data_raw = np.nanmean([estimator.pages[page_no].data_raw for estimator in estimator_list], axis=0)
    result.file_counter = len(estimator_list)
    if result.file_counter > 1 and error_estimate != ErrorEstimate.none:
        # s = stddev = sqrt(1/(n-1)sum(x-<x>)**2)
        # s : corrected sample standard deviation
        for page_no, page in enumerate(result.pages):
            page.error_raw = np.nanstd([estimator.pages[page_no].data_raw for estimator in estimator_list],
                                       axis=0,
                                       ddof=1)

        # if user requested standard error then we calculate it as:
        # S = stderr = stddev / sqrt(n), or in other words,
        # S = s/sqrt(N) where S is the corrected standard deviation of the mean.
        if error_estimate == ErrorEstimate.stderr:
            for page in result.pages:
                page.error_raw /= np.sqrt(result.file_counter)  # np.sqrt() always returns np.float64
    else:
        for page in result.pages:
            page.error_raw = None
    return result
