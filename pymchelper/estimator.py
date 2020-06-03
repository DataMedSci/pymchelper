import copy
from collections import namedtuple
from enum import IntEnum
import logging

import numpy as np
# try to set legacy printing options if working with numpy 1.14 or newer
# on older numpy versions this shouldn't have effect
try:
    np.set_printoptions(legacy="1.13")
except TypeError as e:  # noqa: F841
    pass

logger = logging.getLogger(__name__)


class AxisId(IntEnum):
    x = 0
    y = 1
    z = 2
    diff1 = 3
    diff2 = 4


class MeshAxis(namedtuple('MeshAxis', 'n min_val max_val name unit binning')):
    """
    Scoring mesh axis data.

    It can represent an axis variety of scorers:
    x,y or z in cartesian scoring, r, rho or z in cylindrical.
    An axis represents a sequence of ``n`` numbers, defining linear or logarithmic binning.
    This sequence of numbers is not stored in the memory, but can be generated using data property method.
    ``min_val`` is lowest bin left edge, max_val is highest bin right edge
    ``name`` can be used to define physical quantity (i.e. position, energy, angle).
    ``unit`` gives physical units (i.e. cm, MeV, mrad).

    ``MeshAxis`` is constructed as immutable data structure, thus it is possible
    to set field values only upon object creation. Later they are available for read only.

    >>> x = MeshAxis(n=10, min_val=0.0, max_val=30.0, name="Position", unit="cm", binning=MeshAxis.BinningType.linear)
    >>> x.n, x.min_val, x.max_val
    (10, 0.0, 30.0)
    >>> x.n = 5
    Traceback (most recent call last):
    ...
    AttributeError: can't set attribute

    ``binning`` field (use internal ``BinningType.linear`` or ``BinningType.logarithmic``) can distinguish
    log from linear binning
    """
    class BinningType(IntEnum):
        """
        type of axis generator
        """
        linear = 0
        logarithmic = 1

    @property
    def data(self):
        """
        Generates linear or logarithmic sequence of ``n`` numbers.

        These numbers are middle points of the bins
        defined by ``n``, ``min_val`` and ``max_val`` parameters.

        >>> x = MeshAxis(n=10, min_val=0.0, max_val=10.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> x.data
        array([ 0.5,  1.5,  2.5,  3.5,  4.5,  5.5,  6.5,  7.5,  8.5,  9.5])

        Binning may also consist of one bin:
        >>> x = MeshAxis(n=1, min_val=0.0, max_val=5.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> x.data
        array([ 2.5])

        Logarithmic binning works as well, middle bin points are calculated as geometrical mean.
        Here we define 3 bins: [1,4], [4,16], [16,64].
        >>> x = MeshAxis(n=3, min_val=1.0, max_val=64.0, name="X", unit="cm", binning=MeshAxis.BinningType.logarithmic)
        >>> x.data
        array([  2.,   8.,  32.])

        For the same settings as below linear scale gives as expected different sequence:
        >>> x = MeshAxis(n=3, min_val=1.0, max_val=64.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> x.data
        array([ 11.5,  32.5,  53.5])

        For logarithmic axis min_val has to be positive:
        >>> x = MeshAxis(n=3, min_val=-2.0, max_val=64.0, name="X", unit="cm", binning=MeshAxis.BinningType.logarithmic)
        >>> x.data
        Traceback (most recent call last):
        ...
        Exception: Left edge of first bin (-2) is not positive

        :return:
        """
        if self.max_val < self.min_val:
            raise Exception("Right edge of last bin ({:g}) is smaller than left edge of first bin ({:g})".format(
                self.max_val, self.min_val
            ))
        if self.binning == self.BinningType.linear:
            bin_width = (self.max_val - self.min_val) / self.n
            first_bin_mid = self.min_val + bin_width / 2.0  # arithmetic mean
            last_bin_mid = self.max_val - bin_width / 2.0  # arithmetic mean
            return np.linspace(start=first_bin_mid, stop=last_bin_mid, num=self.n)
        elif self.binning == self.BinningType.logarithmic:
            if self.min_val < 0.0:
                raise Exception("Left edge of first bin ({:g}) is not positive".format(self.min_val))
            q = (self.max_val / self.min_val)**(1.0 / self.n)  # an = a0 q^n
            first_bin_mid = self.min_val * q**0.5  # geometrical mean sqrt(a0 a1) = sqrt( a0 a0 q) = a0 sqrt(q)
            last_bin_mid = self.max_val / q**0.5  # geometrical mean sqrt(an a(n-1)) = sqrt( an an/q) = an / sqrt(q)
            try:
                result = np.geomspace(start=first_bin_mid, stop=last_bin_mid, num=self.n)
            except AttributeError:
                # Python3.2 require numpy older than 1.2, such versions of numpy doesn't have geomspace function
                # in such case we calculate geometrical binning manually
                result = np.exp(np.linspace(start=np.log(first_bin_mid),
                                            stop=np.log(last_bin_mid),
                                            num=self.n))
            return result
        else:
            return None


class ErrorEstimate(IntEnum):
    """
    When averaging data multiple files we could estimate statistical error of scored quantity.
    Such error can be calculated as: none (error information missing), standard error or standard deviation.
    """
    none = 0
    stderr = 1
    stddev = 2


class Page:
    def __init__(self, estimator=None):

        self.estimator = estimator

        self.data_raw = np.array([float("NaN")])  # linear data storage
        self.error_raw = np.array([float("NaN")])  # linear data storage

        self.name = ""
        self.unit = ""

        self.dettyp = None  # Dose, Fluence, LET etc...

        # optional first differential axis
        self.diff_axis1 = MeshAxis(n=1,
                                   min_val=float("NaN"),
                                   max_val=float("NaN"),
                                   name="",
                                   unit="",
                                   binning=MeshAxis.BinningType.linear)

        # optional second differential axis
        self.diff_axis2 = MeshAxis(n=1,
                                   min_val=float("NaN"),
                                   max_val=float("NaN"),
                                   name="",
                                   unit="",
                                   binning=MeshAxis.BinningType.linear)

    def axis(self, axis_id):
        """
        TODO
        """
        if axis_id == AxisId.diff1:
            return self.diff_axis1
        elif axis_id == AxisId.diff2:
            return self.diff_axis2
        elif self.estimator:
            return self.estimator.axis(axis_id)
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
        >>> p = Page(e)
        >>> p.diff_axis1 = MeshAxis(n=10, min_val=0.0, max_val=100.0, name="E", unit="MeV",
        ...                         binning=MeshAxis.BinningType.linear)
        >>> p.dimension
        3

        :return: number of page axes (including differential) which have more than one bin
        """
        if self.estimator:
            return 2 - (self.diff_axis1.n, self.diff_axis2.n).count(1) + self.estimator.dimension
        else:
            return None

    @property
    def data(self):
        """
        3-D view of page data.

        Page data is stored originally in `data_raw` 1-D array.
        This property provides efficient view of data, suitable for numpy-like indexing.

        >>> e = Estimator()
        >>> e.x = MeshAxis(n=2, min_val=0.0, max_val=10.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.z = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> p = Page(estimator=e)
        >>> p.data_raw = np.arange(6)
        >>> p.data.shape
        (2, 3, 1, 1, 1)
        >>> p.data[1, 2, 0, 0, 0]
        5

        :return: reshaped view of ``data_raw``
        """

        if self.estimator:
            return self.data_raw.reshape((self.estimator.x.n, self.estimator.y.n, self.estimator.z.n,
                                          self.diff_axis1.n, self.diff_axis2.n))
        else:
            return None

    @property
    def error(self):
        """
        3-D view of page error

        For more details see ``data`` property.
        :return:
        """
        if self.estimator:
            return self.error_raw.reshape((self.estimator.x.n, self.estimator.y.n, self.estimator.z.n,
                                           self.diff_axis1.n, self.diff_axis2.n))
        else:
            return None

    def plot_axis(self, id):
        """
        Calculate new order of detector axis, axis with data (n>1) comes first
        Axes with constant value goes last.

        Let's take a detector d with YZ scoring.
        >>> e = Estimator()
        >>> e.x = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.z = MeshAxis(n=2, min_val=0.0, max_val=2.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> p = e.pages[0]

        First axis for plotting will be Y (as X axis holds only one bin):
        >>> p.plot_axis(0)
        MeshAxis(n=3, min_val=0.0, max_val=150.0, name='Y', unit='cm', binning=<BinningType.linear: 0>)

        Second axis for plotting will be Z (its the next after Y with n > 1 bins)
        >>> p.plot_axis(1)
        MeshAxis(n=2, min_val=0.0, max_val=2.0, name='Z', unit='cm', binning=<BinningType.linear: 0>)

        Finally the third axis will be X, but it cannot be used for plotting as it has only one bin.
        >>> p.plot_axis(2)
        MeshAxis(n=1, min_val=0.0, max_val=1.0, name='X', unit='cm', binning=<BinningType.linear: 0>)


        :param id: axis number (0, 1, 2, 3 or 4)
        :return: axis object
        """
        plotting_order = (AxisId.x, AxisId.y, AxisId.z, AxisId.diff1, AxisId.diff2)
        variable_axes_id = [i for i in plotting_order if self.axis(i).n > 1]
        constant_axes_id = [i for i in plotting_order if self.axis(i).n == 1]
        plotting_order = variable_axes_id + constant_axes_id
        return self.axis(plotting_order[id])


class Estimator(object):
    """
    Detector data including scoring mesh description.

    This class handles in universal way data generated with MC code.
    It includes data (``data`` and ``data_raw`` fields) and optional errors (``error`` and ``error_raw``).
    Detector holds also up to 3 binning axis (``x``, ``y`` and ``z`` fields).
    Scored quantity can be assigned a ``name`` (i.e. dose) and ``unit`` (i.e. Gy).
    Several other fields are also used:
      - nstat: number of simulated histories
      - counter: number of files read to construct detector object
      - corename: common core part of input files defining a name of detector
      - error_type: none, stderr or stddev - error type

    Detector data can be either read from the file (see ``fromfile`` method in ``io`` module
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
        Create dummy detector object.
        >>> d = Estimator()
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
        self.error_type = ErrorEstimate.none
        self.geotyp = None  # MSH, CYL, etc...

        self.pages = (Page(estimator=self),)  # empty page at the beginning

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
