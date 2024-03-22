"""
Output from the simulation running on multiple processess needs to be agregated.
The simplest way of doing so is to calculated the average of the data.
There are however more sophisticated cases: COUNT scorers needs to be summed up, not averaged.
Phase space data needs to be concatenated, not averaged.
Each of the parallel jobs can have different number of histories, so the weighted average needs to be calculated.
Moreover, in case averaging is employed, we can estimate spread of the data as standard deviation or standard error.

The binary output files from each job may be quite large (even ~GB for scoring in fine 3D mesh), to obtain good
statistics we sometimes parallelise the simulation of hundreds or thousands of jobs (when using HPC clusters).
In such case it's not feasible to load all the data into memory and calculate the average in one go, using standard
functions from numpy library. Instead, we need to calculate the average in an online manner,
i.e. by updating the state of respective aggregator object with each new binary output file read.

Such approach results in a significant reduction of memory usage and is more numerically stable.

This module contains several classes for aggregating data from multiple files:
- Aggregator: base class for all other aggregators
- WeightedStatsAggregator: for calculating weighted mean and variance
- ConcatenatingAggregator: for concatenating data
- SumAggregator: for calculating sum instead of variance
- NoAggregator: for cases when no aggregation is required

All aggregators have `data` and `error` property, which can be used to obtain the result of the aggregation.
The `data` property returns the result of the aggregation: mean, sum or concatenated array.
The `error` property returns the spread of data for WeightedStatsAggregator, and `None` for other aggregators.

The `update` method is used to update the state of the aggregator with new data from the file.
"""

from dataclasses import dataclass, field
import logging
from typing import Union, Optional
import numpy as np
from numpy.typing import ArrayLike


@dataclass
class Aggregator:
    """
    Base class for all aggregators.
    The `data` property returns the result of the aggregation, needs to be implemented in derived classes.
    The `error` function returns the spread of data, can be implemented in derived classes. It's a function,
    not a property as different type of error can be calculated (standard deviation, standard error, etc.).
    Type of errors may be then passed in optional keyword arguments `**kwargs`.
    """

    data: Union[float, ArrayLike] = float('nan')

    def error(self, **kwargs):
        """
        Default implementation of error function, returns None.
        """
        return None


@dataclass
class WeightedStatsAggregator(Aggregator):
    """
    Calculates weighted mean and variance of a sequence of numbers or numpy arrays.

    Good overview of currently known methods to calculate online weighted mean and variance can be found in [2].
    The original method to calculate online mean and variance was proposed by Welford in [1].
    The weighed version of this algoritm is nicely illustrated in [3].
    Here we employ algoritm proposed by West in [4] and descibed in Wikipedia [5].

    [1]  Welford, B. P. (1962). "Note on a method for calculating corrected sums of squares and products".
    Technometrics. 4 (3): 419–420.
    [2] Schubert, Erich, and Michael Gertz. "Numerically stable parallel computation of (co-) variance."
    Proceedings of the 30th international conference on scientific and statistical database management. 2018.
    [3] https://justinwillmert.com/posts/2022/notes-on-calculating-online-statistics/
    [4] West, D. H. D. (1979). "Updating Mean and Variance Estimates: An Improved Method".
    Communications of the ACM. 22 (9): 532-535.
    [5] https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Weighted_incremental_algorithm
    """

    data: Union[float, ArrayLike] = float('nan')

    _accumulator_S: Union[float, ArrayLike] = field(default=float('nan'), repr=False, init=False)
    total_weight: float = 0
    _total_weight_squared: float = 0

    def update(self, value: Union[float, ArrayLike], weight: float = 1.0):

        if weight < 0:
            raise ValueError("Weight must be non-negative")

        # first pass initialization
        if self.total_weight == 0:
            self.data = value * 0
            self._accumulator_S = value * 0

        # W_n = W_{n-1} + w_n
        self.total_weight += weight
        self._total_weight_squared += weight**2

        mean_old = self.data
        # mu_n = (1 - w_n / W_n) * mu_{n-1} + (w_n / W_n) * x_n
        # or in other words:
        # mu_n - mu_{n-1} = (w_n / W_n) * (x_n - mu_{n-1})
        self.data += (weight / self.total_weight) * (value - mean_old)

        self._accumulator_S += weight * (value - self.data) * (value - mean_old)

    @property
    def mean(self):
        return self.data

    @property
    def variance_population(self):
        return self._accumulator_S / self.total_weight

    @property
    def variance_sample(self):
        return self._accumulator_S / (self.total_weight - 1)

    def error(self, **kwargs):
        if 'error_type' in kwargs:
            if kwargs['error_type'] == 'population':
                return self.variance_population
            elif kwargs['error_type'] == 'sample':
                return self.variance_sample
        return None


@dataclass
class ConcatenatingAggregator(Aggregator):
    """
    Class for concatenating numpy arrays
    """

    def update(self, value: Union[float, ArrayLike]):
        ""
        if np.isnan(self.data):
            self.data = value
        else:
            self.data = np.concatenate((self.data, value))


@dataclass
class SumAggregator(Aggregator):
    """
    Class for calculating sum of a sequence of numbers.
    """

    def update(self, value: Union[float, ArrayLike]):
        # first value added
        if np.isnan(self.data):
            self.data = value
        # subsequent values added
        else:
            self.data += value


@dataclass
class NoAggregator(Aggregator):
    """
    Class for cases when no aggregation is required.
    Sets the data to the first value and does not update it.
    """

    def update(self, value: Union[float, ArrayLike]):
        # set value only on first update
        if np.isnan(self.data):
            logging.debug("Setting data to %s", value)
            self.data = value
