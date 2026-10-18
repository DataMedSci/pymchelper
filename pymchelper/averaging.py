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
- WeightedStatsAggregator: for calculating weighted (using weights which not necessarily sums up 1) mean and variance
- ConcatenatingAggregator: for concatenating data
- SumAggregator: for calculating sum instead of variance
- NoAggregator: for cases when no aggregation is required

All aggregators have `data` and `error` property, which can be used to obtain the result of the aggregation.
The `data` property returns the result of the aggregation: mean, sum or concatenated array.
The `error` property returns the spread of data for WeightedStatsAggregator, and `None` for other aggregators.

The `update` method is used to update the state of the aggregator with new data from the file.

For details on how this method is applied to average binary output of the MC codes,
see `fromfilelist` method from `input_output.py` module.
"""

from dataclasses import dataclass, field
import logging
from typing import Union, Optional
import numpy as np
from numpy.typing import ArrayLike, NDArray


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
    _updated: bool = field(default=False, repr=False, init=False)
    skip_nan: bool = False  # if True, NaN values are left out, bin by bin

    def update(self, value: Union[float, ArrayLike], **kwargs):
        """Update the state of the aggregator with new data."""
        raise NotImplementedError(f"Update function not implemented for {self.__class__.__name__}")

    def error(self, **kwargs):
        """Default implementation of error function, returns None."""
        logging.debug("Error calculation not implemented for %s", self.__class__.__name__)

    @property
    def updated(self) -> bool:
        """
        Check if the aggregator was updated. The newly created aggregator is in the state of not being updated.
        That means that no aggregation results are present via `data` or `error` properties.
        We rely on the fact that `data` attribute is set to `nan` on creation of the aggregator object.
        On first call to the `update` method the `data` is being filled with floating point numbers or arrays.
        The `update` method sets also `self._updated` to True.
        """
        if isinstance(self.data, float) and np.isnan(self.data):
            return False
        return self._updated


@dataclass
class WeightedStatsAggregator(Aggregator):
    """
    Calculates weighted mean and variance of a sequence of numbers or numpy arrays.
    We do not use frequency weights (which sums up to 1), the total sum of all weights is not known as
    we are aggregating data from multiple files with different number of histories.
    The aggregation uses single pass loop over all files.

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

    data: Union[float, NDArray[np.float64]] = float('nan')

    _accumulator_S: Union[float, NDArray[np.float64]] = field(default=float('nan'), repr=False, init=False)
    _mean: Union[float, NDArray[np.float64]] = field(default=float('nan'), repr=False, init=False)  # used with skip_nan
    _total_weight_squared: float = field(default=0., repr=False, init=False)
    total_weight: float = 0

    def update(self, value: Union[float, ArrayLike], weight: float = 1.0, **kwargs):
        """
        Update the state of the aggregator with new data.
        Note that the weights are so called "reliability weights", not frequency weights.
        If unsure put here the number of histories from the file if you are aggregating data from multiple files.
        """
        if weight < 0:
            raise ValueError("Weight must be non-negative")
        weight = float(weight)  # readers give primaries as numpy ints, the weight products below would overflow

        if self.skip_nan:
            self._update_skipping_nan(value, weight)
            return

        # first pass initialization, accumulate in float64 whatever the input dtype
        if not self.updated:
            self.data = np.zeros(np.shape(value)) if np.ndim(value) else 0.0
            self._accumulator_S = np.zeros(np.shape(value)) if np.ndim(value) else 0.0
        elif weight == 0:
            return  # contributes nothing, and the S factor below divides by the weight

        # W_n = W_{n-1} + w_n
        self.total_weight += weight
        self._total_weight_squared += weight**2

        # West's update, with d = x_n - mu_{n-1}:
        # mu_n = mu_{n-1} + (w_n / W_n) * d
        # S_n = S_{n-1} + w_n * (1 - w_n / W_n) * d^2, every term >= 0, so S never cancels or goes negative
        # all in place on a single temporary array, scalars rebind instead
        delta = np.subtract(value, self.data, dtype=np.float64)
        delta *= weight / self.total_weight
        self.data += delta
        delta *= delta
        delta *= self.total_weight * (self.total_weight - weight) / weight
        self._accumulator_S += delta

        self._updated = True
        logging.debug("Updated aggregator with value %s and weight %s", value, weight)

    def _update_skipping_nan(self, value: Union[float, ArrayLike], weight: float):
        """
        Same update as above, but each bin has its own total weight:
        a NaN value gets weight 0 in its bin, so it changes neither the mean nor the variance there.
        Bins which got only NaN values end up with total weight 0 and mean NaN.
        """
        value = np.asarray(value, dtype=np.float64)
        weights = np.full(value.shape, weight)
        missing = np.isnan(value)
        weights[missing] = 0.0
        value = np.where(missing, 0.0, value)  # any finite number works here, its weight is 0

        if not self.updated:
            self._mean = np.zeros(value.shape)
            self._accumulator_S = np.zeros(value.shape)
            self.total_weight = np.zeros(value.shape)
            self._total_weight_squared = np.zeros(value.shape)

        self.total_weight += weights
        self._total_weight_squared += weights**2

        # West's update as above, with w_n / W_n set to 0 in bins which have no weight yet
        weight_fraction = np.zeros(value.shape)
        np.divide(weights, self.total_weight, out=weight_fraction, where=self.total_weight > 0)
        delta = value - self._mean
        self._mean += weight_fraction * delta
        self._accumulator_S += weights * (1 - weight_fraction) * delta**2

        self.data = np.where(self.total_weight > 0, self._mean, np.nan)
        self._updated = True

    @property
    def mean(self) -> Union[float, ArrayLike]:
        """Weighted mean of the sample"""
        return self.data

    @property
    def variance_population(self) -> Union[float, ArrayLike]:
        """Biased estimate of the variance"""
        if not self.updated:
            raise ValueError("No data to calculate variance")
        if np.all(self.total_weight <= 0):
            raise ValueError("Total weight must be positive")
        with np.errstate(divide='ignore', invalid='ignore'):  # bins without weight give NaN
            return self._accumulator_S / self.total_weight

    @property
    def variance_sample(self) -> Union[float, ArrayLike]:
        """
        Unbiased estimate of the variance.
        The bias of the weighted estimator if (1 - sum w_i^2 / W_n^2), or in other words:
        1 - "sum of squares of weights" / "square of sum of weights".
        For all equal weights the bias is 1 - n * w^2/((n * w)^2) = 1 - 1/n which
        leads to the well known formula for the sample variance.
        Here we use the weighted version of the formula.
        """
        if not self.updated:
            raise ValueError("No data to calculate variance")
        if np.all(self.total_weight <= 0):
            raise ValueError("Total weight must be positive")
        with np.errstate(divide='ignore', invalid='ignore'):  # bins without weight, or with one value, give NaN
            return self._accumulator_S / (self.total_weight - (self._total_weight_squared / self.total_weight))

    @property
    def stddev(self) -> Union[float, ArrayLike]:
        """Standard deviation of the sample"""
        return np.sqrt(self.variance_sample)

    @property
    def stderr(self) -> Union[float, ArrayLike]:
        """
        Standard error of the sample.
        For weighted data it is calculated as:
        stddev * sqrt(sum w_i^2) / sum w_i
        For equal weights it reduces via sqrt( n * w^2) / (n * w) = stddev / sqrt(n)
        """
        with np.errstate(divide='ignore', invalid='ignore'):  # bins without weight give NaN
            return self.stddev * np.sqrt(self._total_weight_squared) / self.total_weight

    def error(self, **kwargs) -> Optional[Union[float, ArrayLike]]:
        """
        Error calculation function, can be used to calculate standard deviation or standard error.
        Type of error may be requested by `error_type` keyword argument with `stddev` or `stderr` values.
        For other values or if the keyword argument is not present, None is returned.
        """
        logging.debug("Calculating error with kwargs: %s", kwargs)
        if 'error_type' in kwargs:
            if kwargs['error_type'] == 'stddev':
                return self.stddev
            if kwargs['error_type'] == 'stderr':
                return self.stderr
        return None


@dataclass
class ConcatenatingAggregator(Aggregator):
    """
    Class for concatenating numpy arrays.
    The arrays are collected in a list and joined once, when `data` is read,
    so every value is copied once, however many files are merged.
    """

    _parts: list = field(default_factory=list, repr=False, init=False)

    def update(self, value: Union[float, ArrayLike], **kwargs):
        """Update the state of the aggregator with new data."""
        self._parts.append(value)
        self._updated = True

    @property
    def data(self) -> Union[float, ArrayLike]:
        """All arrays collected so far, joined into one"""
        if len(self._parts) == 0:
            return float('nan')
        if len(self._parts) > 1:
            joined = np.concatenate(self._parts)
            self._parts = [joined]
        return self._parts[0]

    @data.setter
    def data(self, value: Union[float, ArrayLike]):
        """Setting data replaces everything collected so far (the dataclass init sets it to NaN, i.e. nothing)"""
        self._parts = []
        if isinstance(value, float) and np.isnan(value):
            return
        self._parts.append(value)


@dataclass
class SumAggregator(Aggregator):
    """Class for calculating sum of a sequence of numbers."""

    def update(self, value: Union[float, ArrayLike], **kwargs):
        """Update the state of the aggregator with new data."""
        # first value added
        if not self.updated:
            self.data = value
        # subsequent values added, NaN taken as 0 unless the bin has only NaN values
        elif self.skip_nan:
            missing_so_far = np.isnan(self.data)
            missing_now = np.isnan(value)
            previous_values = np.where(missing_so_far, 0.0, self.data)
            new_values = np.where(missing_now, 0.0, value)
            total = previous_values + new_values
            missing_in_all_files = missing_so_far & missing_now
            self.data = np.where(missing_in_all_files, np.nan, total)
        # subsequent values added
        else:
            self.data = np.add(self.data, value)
        self._updated = True


@dataclass
class NoAggregator(Aggregator):
    """
    Class for cases when no aggregation is required.
    Sets the data to the first value and does not update it.
    """

    def update(self, value: Union[float, ArrayLike], **kwargs):
        """Update the state of the aggregator with new data."""
        # set value only on first update
        if not self.updated:
            logging.debug("Setting data to %s", value)
            self.data = value
        self._updated = True
