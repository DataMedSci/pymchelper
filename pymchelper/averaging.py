from dataclasses import dataclass
from typing import Union, Optional
from numpy.typing import ArrayLike

# resource https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
# also


@dataclass
class Aggregator:

    data: Union[float, ArrayLike] = float('nan')

    def error(self, **kwargs):
        if isinstance(self.data, float):
            return np.nan
        else:
            return np.zeros_like(self.data) * np.nan


@dataclass
class WeightedStatsAggregator(Aggregator):
    """
    Class for calculating weighted mean of a sequence of numbers.
    Accoring to https://justinwillmert.com/posts/2022/notes-on-calculating-online-statistics/
    Heavily based on Welford's algorithm [1]
    [1]  Welford, B. P. (1962). "Note on a method for calculating corrected sums of squares and products".
    Technometrics. 4 (3): 419–420.
    See also:
    [2] Schubert, Erich, and Michael Gertz.
    "Numerically stable parallel computation of (co-) variance."
    Proceedings of the 30th international conference on scientific and statistical database management. 2018.
    """
    data: Union[float, ArrayLike] = float('nan')
    accumulator_S: Union[float, ArrayLike] = float('nan')
    temp: Union[float, ArrayLike] = float('nan')
    total_weight: float = 0
    total_weight_squared: float = 0

    def update(self, value: Union[float, ArrayLike], weight: float = 1.0):
        if weight < 0:
            raise ValueError("Weight must be non-negative")

        # first pass initialization
        if self.total_weight == 0:
            self.data = value * 0
            self.accumulator_S = value * 0

        # W_n = W_{n-1} + w_n
        self.total_weight += weight
        self.total_weight_squared += weight**2

        mean_old = self.data
        # # mu_n = (1 - w_n / W_n) * mu_{n-1} + (w_n / W_n) * x_n
        # first_part = (1 - weight / self.total_weight) * self.mean
        # second_part = (weight / self.total_weight) * value
        self.data += (weight / self.total_weight) * (value - mean_old)

        self.accumulator_S += weight * (value - self.data) * (value - mean_old)

    @property
    def mean(self):
        return self.data

    @property
    def variance_population(self):
        return self.accumulator_S / self.total_weight

    @property
    def variance_sample(self):
        return self.accumulator_S / (self.total_weight - 1)

    def error(self, **kwargs):
        if 'error_type' in kwargs:
            if kwargs['error_type'] == 'population':
                return self.variance_population
            elif kwargs['error_type'] == 'sample':
                return self.variance_sample
            else:
                if isinstance(self.data, float):
                    return np.nan
                else:
                    return np.zeros_like(self.data) * np.nan


@dataclass
class ConcatenatingAggregator(Aggregator):
    """
    Class for concatenating numpy arrays
    """

    def update(self, value: Union[float, ArrayLike]):
        if np.isnan(data):
            self.data = value
        else:
            self.data = np.concatenate((self.data, value))


@dataclass
class SumAggregator(Aggregator):
    """
    Class for calculating sum of a sequence of numbers.
    """

    def update(self, value: Union[float, ArrayLike]):
        if np.isnan(self.total):
            self.data = value
        else:
            self.data += value
