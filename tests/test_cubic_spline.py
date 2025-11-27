import numpy as np
import pytest
from scipy.interpolate import interp1d

from pymchelper.utils.spline import CubicSpline1D, cubic_interpolate


def make_random_data(n=50, seed=123):
    """Generate random sorted data for testing."""
    rng = np.random.default_rng(seed)
    x = np.sort(rng.uniform(0.0, 10.0, size=n))
    y = np.sin(x) + 0.1 * rng.normal(size=n)
    return x, y


@pytest.mark.parametrize("n_points", [10, 100])
def test_cubic_spline_matches_scipy(n_points):
    """Test that our cubic spline matches SciPy's interp1d with kind='cubic'."""
    x, y = make_random_data()
    xp = np.linspace(x[0], x[-1], n_points)

    # SciPy cubic
    sp = interp1d(x, y, kind="cubic")
    y_sp = sp(xp)

    # Our implementation
    cs = CubicSpline1D(x, y)
    y_cs = cs(xp)

    # Allow small numeric differences
    np.testing.assert_allclose(y_cs, y_sp, rtol=3e-2, atol=1e-2)


def test_scalar_vs_vector_consistency():
    """Test that scalar and vector inputs produce consistent results."""
    x, y = make_random_data()
    cs = CubicSpline1D(x, y)
    xv = np.linspace(x[0], x[-1], 20)
    y_vec = cs(xv)
    y_scalars = np.array([cs(float(v)) for v in xv])
    np.testing.assert_allclose(y_vec, y_scalars, rtol=1e-12, atol=0.0)


def test_direct_function_matches_wrapper():
    """Test that cubic_interpolate function matches CubicSpline1D wrapper."""
    x, y = make_random_data()
    xv = np.linspace(x[0], x[-1], 25)
    y1 = cubic_interpolate(xv, x, y)
    cs = CubicSpline1D(x, y)
    y2 = cs(xv)
    np.testing.assert_allclose(y1, y2, rtol=1e-12, atol=0.0)
