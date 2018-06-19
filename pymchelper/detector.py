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
    none = 0
    stderr = 1
    stddev = 2


class Detector:
    """
    Detector data including scoring mesh description.

    This class handles in universal way data generated with MC code.
    It includes data (``data`` and ``data_raw`` fields) and optinal errors (``error`` and ``error_raw``).
    Detector holds also up to 3 binning axis (``x``, ``y`` and ``z`` fields).
    Scored quantity can be assigned a ``name`` (i.e. dose) and ``unit`` (i.e. Gy).
    Several other fields are also used:
      - nstat: number of simulated histories
      - counter: number of files read to construct detector object
      - corename: common core part of input files defining a name of detector
      - error_type: none, stderr or stddev - error type

    Detector data can be either read from the file (see ``fromfile`` method in ``io`` module
    or constructed directly:

    >>> d = Detector()
    >>> d.x = MeshAxis(n=2, min_val=0.0, max_val=10.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
    >>> d.x.data
    array([ 2.5,  7.5])
    >>> d.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
    >>> d.y.data
    array([  25.,   75.,  125.])
    >>> d.z = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)
    >>> d.z.data
    array([ 0.5])
    >>> d.data_raw = np.arange(6)
    >>> d.data.shape
    (2, 3, 1)
    >>> d.data
    array([[[0],
            [1],
            [2]],
           [[3],
            [4],
            [5]]])

    """

    def __init__(self):
        """
        Create dummy detector object.

        >>> d = Detector()
        >>> d.x.data
        array([ nan])
        >>> d.y.data
        array([ nan])
        >>> d.z.data
        array([ nan])
        >>> d.data.shape
        (1, 1, 1)
        >>> d.data
        array([[[ nan]]])
        """
        self.x = MeshAxis(n=1,
                          min_val=float("NaN"),
                          max_val=float("NaN"),
                          name="",
                          unit="",
                          binning=MeshAxis.BinningType.linear)
        self.y = self.x
        self.z = self.x
        self.data_raw = np.array([float("NaN")])
        self.error_raw = np.array([float("NaN")])
        self.name = ""
        self.unit = ""
        self.nstat = 0  # number of histories simulated
        self.counter = 0  # number of files read
        self.corename = ""  # common core for paths of contributing files
        self.error_type = ErrorEstimate.none

    def axis(self, id):
        """
        Mesh axis selector method based on integer id's.

        Instead of getting mesh axis data by calling `d.x`, `d.y` or `d.z` (assuming `d` an object of `Detector`
        class) we can get that data by calling `d.axis(0)`, `d.axis(1)` or `d.axis(2)`. See for example:
        >>> d = Detector()
        >>> d.x = MeshAxis(n=2, min_val=0.0, max_val=10.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.z = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.axis(1)
        MeshAxis(n=3, min_val=0.0, max_val=150.0, name='Y', unit='cm', binning=<BinningType.linear: 0>)

        :param id: axis id (0, 1 or 2)
        :return: MeshAxis object
        """
        if id == 0:
            return self.x
        elif id == 1:
            return self.y
        elif id == 2:
            return self.z
        return None

    def plot_axis(self, id):
        """
        Calculate new order of detector axis, axis with data (n>1) comes first
        Axes with constant value goes last.

        Let's take a detector d with YZ scoring.
        >>> d = Detector()
        >>> d.x = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.z = MeshAxis(n=2, min_val=0.0, max_val=2.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)

        First axis for plotting will be Y (as X axis holds only one bin):
        >>> d.plot_axis(0)
        MeshAxis(n=3, min_val=0.0, max_val=150.0, name='Y', unit='cm', binning=<BinningType.linear: 0>)

        Second axis for plotting will be Z (its the next after Y with n > 1 bins)
        >>> d.plot_axis(1)
        MeshAxis(n=2, min_val=0.0, max_val=2.0, name='Z', unit='cm', binning=<BinningType.linear: 0>)

        Finally the third axis will be X, but it cannot be used for plotting as it has only one bin.
        >>> d.plot_axis(2)
        MeshAxis(n=1, min_val=0.0, max_val=1.0, name='X', unit='cm', binning=<BinningType.linear: 0>)


        :param id: axis number (0, 1 or 2)
        :return: axis object
        """
        plotting_order = (0, 1, 2)
        if self.dimension == 1:
            if self.x.n > 1:
                plotting_order = (0, 1, 2)  # X variable; Y,Z constant
            elif self.y.n > 1:
                plotting_order = (1, 0, 2)  # Y variable; X,Z constant
            elif self.z.n > 1:
                plotting_order = (2, 0, 1)  # Z variable; X,Y constant
        elif self.dimension == 2:
            if self.x.n == 1:
                plotting_order = (1, 2, 0)  # Y,Z variable; X constant
            elif self.y.n == 1:
                plotting_order = (0, 2, 1)  # X,Z variable; Y constant
            elif self.z.n == 1:
                plotting_order = (0, 1, 2)  # X,Y variable; Z constant

            # when SH12A differential scorer is used, we assume that differential
            # quantity should go last
            # a special case is when when X-constant, Y-differential, Z-scored
            # we need to swap X and Z to guarantee that the differential quantity will be last
            if hasattr(self, 'dif_axis') and self.dif_axis == 1:
                plotting_order = (2, 1, 0)

        return self.axis(plotting_order[id])

    @property
    def dimension(self):
        """
        Let's take again detector d with YZ scoring.
        >>> d = Detector()
        >>> d.x = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.z = MeshAxis(n=2, min_val=0.0, max_val=2.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.dimension
        2

        :return: number of axes which have more than one point
        """
        return 3 - (self.x.n, self.y.n, self.z.n).count(1)

    @property
    def data(self):
        """
        3-D view of detector data.

        Detector data are stored originally in `data_raw` 1-D array.
        This property provides efficient view of detector data, suitable for numpy-like indexing.

        >>> d = Detector()
        >>> d.x = MeshAxis(n=2, min_val=0.0, max_val=10.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.z = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> d.data_raw = np.arange(6)
        >>> d.data.shape
        (2, 3, 1)
        >>> d.data[1, 2, 0]
        5

        :return: reshaped view of ``data_raw``
        """
        return self.data_raw.reshape((self.x.n, self.y.n, self.z.n))

    @property
    def error(self):
        """
        3-D view of detector error

        For more details see ``data`` property.
        :return:
        """
        return self.error_raw.reshape((self.x.n, self.y.n, self.z.n))


def average_with_nan(detector_list, error_estimate=ErrorEstimate.stderr):
    """
    Calculate average detector object, excluding malformed data (NaN) from averaging.
    :param detector_list:
    :param error_estimate:
    :return:
    """
    # TODO add compatibility check
    result = Detector()
    result.counter = len(detector_list)
    result.data_raw = np.nanmean([det.data_raw for det in detector_list], axis=0)
    if result.counter > 1 and error_estimate != ErrorEstimate.none:
        # s = stddev = sqrt(1/(n-1)sum(x-<x>)**2)
        # s : corrected sample standard deviation
        result.error_raw = np.nanstd([det.data_raw for det in detector_list], axis=0, ddof=1)

        # if user requested standard error then we calculate it as:
        # S = stderr = stddev / sqrt(n), or in other words,
        # S = s/sqrt(N) where S is the corrected standard deviation of the mean.
        if error_estimate == ErrorEstimate.stderr:
            result.error_raw /= np.sqrt(result.counter)  # np.sqrt() always returns np.float64
    else:
        result.error_raw = np.zeros_like(result.data_raw)
    return result
