from collections import namedtuple
from enum import IntEnum

import numpy as np


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


class AxisId(IntEnum):
    x = 0
    y = 1
    z = 2
    diff1 = 3
    diff2 = 4
