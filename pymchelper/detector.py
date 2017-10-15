from collections import namedtuple
from enum import IntEnum
import logging

import numpy as np

logger = logging.getLogger(__name__)


class MeshAxis(namedtuple('MeshAxis', 'n min_val max_val name unit binning')):
    """
    Scoring mesh axis
    """
    class BinningType(IntEnum):
        """
        type of axis generator
        """
        linear = 0
        logarithmic = 1

    @property
    def data(self):
        if self.binning == self.BinningType.linear:
            bin_width = (self.max_val - self.min_val) / self.n
            first_bin_mid = self.min_val + bin_width / 2.0
            last_bin_mid = self.max_val - bin_width / 2.0
            return np.linspace(start=first_bin_mid, stop=last_bin_mid, num=self.n)
        elif self.binning == self.BinningType.logarithmic:
            q = (self.max_val / self.min_val)**(1.0 / self.n)  # an = a0 q^n
            first_bin_mid = self.min_val * q**0.5  # sqrt(a0 a1) = sqrt( a0 a0 q) = a0 sqrt(q)
            last_bin_mid = self.max_val / q**0.5  # sqrt(an a(n-1)) = sqrt( an an/q) = an / sqrt(q)
            return np.geomspace(start=first_bin_mid, stop=last_bin_mid, num=self.n)
        else:
            return None


class ErrorEstimate(IntEnum):
    none = 0
    stderr = 1
    stddev = 2


class Detector:
    def __init__(self):
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
        self.counter = 0  # number of files read
        self.corename = ""  # common core for paths of contributing files
        self.error_type = ErrorEstimate.none

    def axis(self, id):
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
        Axes with constant value goes last
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

        return self.axis(plotting_order[id])

    @property
    def data(self):
        return self.data_raw.reshape((self.x.n, self.y.n, self.z.n))

    @property
    def error(self):
        return self.error_raw.reshape((self.x.n, self.y.n, self.z.n))

    @property
    def dimension(self):
        # number of axes which have more than one point
        return 3 - (self.x.n, self.y.n, self.z.n).count(1)


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
    result.data_raw = np.nanmean((det.data_raw for det in detector_list), axis=0)
    if result.counter > 1 and error_estimate != ErrorEstimate.none:
        # s = stddev = sqrt(1/(n-1)sum(x-<x>)**2)
        # s : corrected sample standard deviation
        result.error_raw = np.nanstd((det.data_raw for det in detector_list), axis=0, ddof=1)

        # if user requested standard error then we calculate it as:
        # S = stderr = stddev / sqrt(n), or in other words,
        # S = s/sqrt(N) where S is the corrected standard deviation of the mean.
        if error_estimate == ErrorEstimate.stderr:
            result.error_raw /= np.sqrt(result.counter)  # np.sqrt() always returns np.float64
    else:
        result.error_raw = np.zeros_like(result.data_raw)
    return result
