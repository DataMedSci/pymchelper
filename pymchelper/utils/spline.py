from typing import Sequence, Union
import numpy as np


def cubic_interpolate(x0: Union[float, np.ndarray], x: np.ndarray, y: np.ndarray) -> Union[float, np.ndarray]:
    """Natural cubic spline interpolation.

    Interpolates value(s) at x0 based on knots x, y using a natural cubic spline.
    Assumes x is sorted in ascending order.
    """
    xdiff = np.diff(x)
    dydx = np.diff(y)
    dydx = dydx / xdiff

    n = len(x)
    w = np.empty(n - 1, float)
    z = np.empty(n, float)

    w[0] = 0.0
    z[0] = 0.0
    for i in range(1, n - 1):
        m = xdiff[i - 1] * (2 - w[i - 1]) + 2 * xdiff[i]
        w[i] = xdiff[i] / m
        z[i] = (6 * (dydx[i] - dydx[i - 1]) - xdiff[i - 1] * z[i - 1]) / m
    z[-1] = 0.0

    for i in range(n - 2, -1, -1):
        z[i] = z[i] - w[i] * z[i + 1]

    def _interp_one(x0_one: float) -> float:
        """Interpolate a single value."""
        # find interval index (requires x sorted)
        index = x.searchsorted(x0_one)
        index = int(np.clip(index, 1, n - 1))

        xi1, xi0 = x[index], x[index - 1]
        yi1, yi0 = y[index], y[index - 1]
        zi1, zi0 = z[index], z[index - 1]
        hi1 = xi1 - xi0

        # cubic formula
        f0 = (
            zi0 / (6 * hi1) * (xi1 - x0_one) ** 3
            + zi1 / (6 * hi1) * (x0_one - xi0) ** 3
            + (yi1 / hi1 - zi1 * hi1 / 6) * (x0_one - xi0)
            + (yi0 / hi1 - zi0 * hi1 / 6) * (xi1 - x0_one)
        )
        return float(f0)

    if np.isscalar(x0):
        return _interp_one(float(x0))
    x0_arr = np.asarray(x0, dtype=float)
    return np.array([_interp_one(float(v)) for v in x0_arr])


class CubicSpline1D:
    """Callable cubic spline interpolator for 1D data.

    Wraps `cubic_interpolate` to provide a SciPy-like callable.
    """

    def __init__(self, x: Sequence[float], y: Sequence[float]):
        self.x = np.asarray(x, dtype=float)
        self.y = np.asarray(y, dtype=float)

    def __call__(self, x0: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        return cubic_interpolate(x0, self.x, self.y)
