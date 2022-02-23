import copy
from enum import IntEnum
import logging

import numpy as np
from pymchelper.axis import MeshAxis, AxisId

logger = logging.getLogger(__name__)


class ErrorEstimate(IntEnum):
    """
    When averaging data multiple files we could estimate statistical error of scored quantity.
    Such error can be calculated as: none (error information missing), standard error or standard deviation.
    """
    none = 0
    stderr = 1
    stddev = 2


class Estimator(object):
    """
    Estimator data including scoring mesh description.

    This class handles in universal way data generated with MC code.
    It includes data (``data`` and ``data_raw`` fields) and optional errors (``error`` and ``error_raw``).
    Estimator holds also up to 3 binning axis (``x``, ``y`` and ``z`` fields).
    Scored quantity can be assigned a ``name`` (i.e. dose) and ``unit`` (i.e. Gy).
    Several other fields are also used:
    - nstat: number of simulated histories
    - counter: number of files read to construct detector object
    - corename: common core part of input files defining a name of detector
    - error_type: none, stderr or stddev - error type

    Estimator data can be either read from the file (see ``fromfile`` method in ``input_output`` module
    or constructed directly:

    >>> d = Estimator()
    >>> d.x = MeshAxis(n=2, min_val=0.0, max_val=10.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
    >>> d.x.data
    array([ 2.5,  7.5])
    >>> d.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
    >>> d.y.data
    array([  25.,   75.,  125.])
    >>> d.z = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)
    >>> d.z.data
    array([ 0.5])
    """

    def __init__(self):
        """
        Create dummy estimator object.
        >>> e = Estimator()
        """
        self.x = MeshAxis(n=1,
                          min_val=float("NaN"),
                          max_val=float("NaN"),
                          name="",
                          unit="",
                          binning=MeshAxis.BinningType.linear)
        self.y = self.x
        self.z = self.x

        self.number_of_primaries = 0  # number of histories simulated
        self.file_counter = 0  # number of files read
        self.file_corename = ""  # common core for paths of contributing files
        self.file_format = ""  # binary file format of the input files
        self.error_type = ErrorEstimate.none
        self.geotyp = None  # MSH, CYL, etc...

        self.pages = ()  # empty tuple of pages at the beginning

    def add_page(self, page):
        """
        Add a page to the estimator object.
        New copy of page is made and page estimator pointer is set to the estimator object holding this page.
        :param page:
        :return: None
        """
        new_page = copy.deepcopy(page)
        new_page.estimator = self
        self.pages += (new_page,)

    def axis(self, axis_id):
        """
        Mesh axis selector method based on integer id's.

        Instead of getting mesh axis data by calling `d.x`, `d.y` or `d.z` (assuming `d` an object of `Detector`
        class) we can get that data by calling `d.axis(0)`, `d.axis(1)` or `d.axis(2)`. See for example:
        >>> d = Estimator()
        >>> d.x = MeshAxis(n=2, min_val=0.0, max_val=10.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.z = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.axis(1)
        MeshAxis(n=3, min_val=0.0, max_val=150.0, name='Y', unit='cm', binning=<BinningType.linear: 0>)

        :param axis_id: axis id (0, 1 or 2)
        :return: MeshAxis object
        """
        if axis_id == AxisId.x:
            return self.x
        elif axis_id == AxisId.y:
            return self.y
        elif axis_id == AxisId.z:
            return self.z
        return None

    @property
    def dimension(self):
        """
        Let's take again detector d with YZ scoring.
        >>> e = Estimator()
        >>> e.x = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.z = MeshAxis(n=2, min_val=0.0, max_val=2.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.dimension
        2

        :return: number of axes (among X,Y,Z) which have more than one bin
        """
        return 3 - (self.x.n, self.y.n, self.z.n).count(1)


def average_with_nan(estimator_list, error_estimate=ErrorEstimate.stderr):
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
    for page_no, page in enumerate(result.pages):
        page.data_raw = np.nanmean([estimator.pages[page_no].data_raw for estimator in estimator_list], axis=0)
    result.file_counter = len(estimator_list)
    if result.file_counter > 1 and error_estimate != ErrorEstimate.none:
        # s = stddev = sqrt(1/(n-1)sum(x-<x>)**2)
        # s : corrected sample standard deviation
        for page_no, page in enumerate(result.pages):
            page.error_raw = np.nanstd([estimator.pages[page_no].data_raw for estimator in estimator_list],
                                       axis=0, ddof=1)

        # if user requested standard error then we calculate it as:
        # S = stderr = stddev / sqrt(n), or in other words,
        # S = s/sqrt(N) where S is the corrected standard deviation of the mean.
        if error_estimate == ErrorEstimate.stderr:
            for page in result.pages:
                page.error_raw /= np.sqrt(result.file_counter)  # np.sqrt() always returns np.float64
    else:
        for page in result.pages:
            page.error_raw = np.zeros_like(page.data_raw)
    return result
