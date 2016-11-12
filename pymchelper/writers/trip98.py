import time
import logging
import math
from copy import deepcopy

from scipy.optimize import leastsq
import numpy as np

logger = logging.getLogger(__name__)


class TripCubeWriter:
    def __init__(self, filename, options):
        self.output_corename = filename

    def write(self, detector):
        from pymchelper.shieldhit.detector.detector_type import SHDetType

        pixel_size_x = (detector.xmax - detector.xmin) / detector.nx
        pixel_size_z = (detector.zmax - detector.zmin) / detector.nz

        if detector.dettyp == SHDetType.dose:

            from pytrip import dos

            cube = dos.DosCube()
            cube.create_empty_cube(
                1.0, detector.nx, detector.ny, detector.nz, pixel_size=pixel_size_x, slice_distance=pixel_size_z)

            # .dos dose cubes are usually in normalized integers,
            # where "1000" equals 100.0 % dose.
            # The next are also the defaults, but just to be clear
            # this is specifially set.
            cube.data_type = "integer"
            cube.bytes = 2
            cube.pydata_type = np.int16

            cube.cube = detector.data.reshape(detector.nx, detector.ny, detector.nz)

            if detector.tripdose >= 0.0 and detector.tripntot > 0:
                cube.cube = (cube.cube * detector.tripntot * 1.602e-10) / detector.tripdose * 1000.0
            else:
                cube.cube = (cube.cube / cube.cube.max()) * 1200.0

            cube.write(self.output_corename)

        elif detector.dettyp in (SHDetType.dlet, SHDetType.tlet, SHDetType.dletg, SHDetType.tletg):

            from pytrip import let

            cube = let.LETCube()
            cube.create_empty_cube(
                1.0, detector.nx, detector.ny, detector.nz, pixel_size=pixel_size_x, slice_distance=pixel_size_z)

            # .dosemlet.dos LET cubes are usually in 32 bit floats.
            cube.data_type = "float"
            cube.bytes = 4
            cube.pydata_type = np.float32

            # need to redo the cube, since by default np.float32 are allocated.
            # When https://github.com/pytrip/pytrip/issues/35 is fixed,
            # then this should not be needed.
            cube.cube = np.ones((cube.dimz, cube.dimy, cube.dimx), dtype=cube.pydata_type) * (1.0)

            cube.cube = detector.data.reshape(detector.nx, detector.ny, detector.nz)
            cube.cube *= 0.1  # MeV/cm -> keV/um

            cube.write(self.output_corename)

        else:
            logger.error("Tripcube target is only allowed with dose- or LET-type detectors.")
            raise Exception("Illegal detector for tripcube.")


"""
Constrained multivariate Levenberg-Marquardt optimization
"""


def internal2external_grad(xi, bounds):
    """
    Calculate the internal to external gradiant

    Calculates the partial of external over internal

    """

    ge = np.empty_like(xi)

    for i, (v, bound) in enumerate(zip(xi, bounds)):

        a = bound[0]  # minimum
        b = bound[1]  # maximum

        if a is None and b is None:  # No constraints
            ge[i] = 1.0

        elif b is None:  # only min
            ge[i] = v / np.sqrt(v**2 + 1)

        elif a is None:  # only max
            ge[i] = -v / np.sqrt(v**2 + 1)

        else:  # both min and max
            ge[i] = (b - a) * np.cos(v) / 2.

    return ge


def i2e_cov_x(xi, bounds, cov_x):
    grad = internal2external_grad(xi, bounds)
    grad = grad = np.atleast_2d(grad)
    return np.dot(grad.T, grad) * cov_x


def internal2external(xi, bounds):
    """ Convert a series of internal variables to external variables"""

    xe = np.empty_like(xi)

    for i, (v, bound) in enumerate(zip(xi, bounds)):

        a = bound[0]  # minimum
        b = bound[1]  # maximum

        if a is None and b is None:  # No constraints
            xe[i] = v

        elif b is None:  # only min
            xe[i] = a - 1. + np.sqrt(v**2. + 1.)

        elif a is None:  # only max
            xe[i] = b + 1. - np.sqrt(v**2. + 1.)

        else:  # both min and max
            xe[i] = a + ((b - a) / 2.) * (np.sin(v) + 1.)

    return xe


def external2internal(xe, bounds):
    """ Convert a series of external variables to internal variables"""

    xi = np.empty_like(xe)

    for i, (v, bound) in enumerate(zip(xe, bounds)):

        a = bound[0]  # minimum
        b = bound[1]  # maximum

        if a is None and b is None:  # No constraints
            xi[i] = v

        elif b is None:  # only min
            xi[i] = np.sqrt((v - a + 1.)**2. - 1)

        elif a is None:  # only max
            xi[i] = np.sqrt((b - v + 1.)**2. - 1)

        else:  # both min and max
            xi[i] = np.arcsin((2. * (v - a) / (b - a)) - 1.)

    return xi


def err(p, bounds, efunc, args):
    pe = internal2external(p, bounds)  # convert to external variables
    return efunc(pe, *args)


def calc_cov_x(infodic, p):
    """
    Calculate cov_x from fjac, ipvt and p as is done in leastsq
    """

    fjac = infodic['fjac']
    ipvt = infodic['ipvt']
    n = len(p)

    # adapted from leastsq function in scipy/optimize/minpack.py
    perm = np.take(np.eye(n), ipvt - 1, 0)
    r = np.triu(np.transpose(fjac)[:n, :])
    R = np.dot(r, perm)
    try:
        cov_x = np.linalg.inv(np.dot(np.transpose(R), R))
    except np.linalg.LinAlgError:
        cov_x = None
    return cov_x


def leastsqbound(func, x0, bounds, args=(), **kw):
    """
    Constrained multivariant Levenberg-Marquard optimization

    Minimize the sum of squares of a given function using the
    Levenberg-Marquard algorithm. Contraints on parameters are inforced using
    variable transformations as described in the MINUIT User's Guide by
    Fred James and Matthias Winkler.

    Parameters:

    * func      functions to call for optimization.
    * x0        Starting estimate for the minimization.
    * bounds    (min,max) pair for each element of x, defining the bounds on
                that parameter.  Use None for one of min or max when there is
                no bound in that direction.
    * args      Any extra arguments to func are places in this tuple.

    Returns: (x,{cov_x,infodict,mesg},ier)

    Return is described in the scipy.optimize.leastsq function.  x and con_v
    are corrected to take into account the parameter transformation, infodic
    is not corrected.

    Additional keyword arguments are passed directly to the
    scipy.optimize.leastsq algorithm.

    """
    # check for full output
    if "full_output" in kw and kw["full_output"]:
        full = True
    else:
        full = False

    # convert x0 to internal variables
    i0 = external2internal(x0, bounds)

    # perfrom unconstrained optimization using internal variables
    r = leastsq(err, i0, args=(bounds, func, args), **kw)

    # unpack return convert to external variables and return
    if full:
        xi, cov_xi, infodic, mesg, ier = r
        xe = internal2external(xi, bounds)
        cov_xe = i2e_cov_x(xi, bounds, cov_xi)
        # XXX correct infodic 'fjac','ipvt', and 'qtf'
        return xe, cov_xe, infodic, mesg, ier

    else:
        xi, ier = r
        xe = internal2external(xi, bounds)
        return xe, ier


# Method fitting the lateral dose distribution
def _lateral_fit(left_radii, radial_dose_scaled, depth, energy):
    """
    Fitting for lateral dose distribution
    Fits the lateral dose scaled with the radius using a double Gaussian by the use of Levenberg-Marquardt optimization

    Parameters:
    * radii        radius values corresponding to dose
    * dose         dose D(r)
    * dose_scaled  dose times the radii D(r)*r
    * depth        only used for graphing
    * energy       only used for graphing

    Returns: (x,{cov_x,infodict,mesg},ier)

    """

    def residuals(p, y, x):  # objective function for minimization (vector function)
        err = y - peval(x, mu, p)
        return err

    def peval(x, mu, p):  # The model function: Two gaussians (sum), the mean mu is locked
        # In guideline with a similar routine for TRiP by U. Weber,
        # the function is scaled with the radius to fit D(r)*r /TPR
        return (p[0] * np.exp(-((x - mu)**2) / (2 * p[1]**2)) + p[2] * np.exp(-((x - mu)**2) / (2 * p[3]**2))) * x

    x = left_radii
    y = radial_dose_scaled
    # Calculate initial guesses #
    a1 = y.max()  # guess for the amplitude of the first gaussian
    mu = 0  # set the mean to zero - a guess would be: sum(x*y)/sum(y)
    if sum(y) == 0:  # check if denominator is 0
        sigma1 = 1e5
    else:
        sigma1 = np.sqrt(abs(sum((x - mu)**2 * y) / sum(y)))  # guess for the deviation
    a2 = deepcopy(a1) * 0.05  # guess for the  amplitude of the second gaussian
    sigma2 = 2  # guess for the deviation of the second gaussian
    sigma2 = deepcopy(sigma1) * 5.0
    # Collect the guesses in an array
    p0 = np.asarray([a1, sigma1, a2, sigma2])
    bounds = [(0, 1e6), (0, 1e6), (0, 1e6), (0, 1e6)]  # set bound for the parameters, they should be non-negative
    plsq = leastsqbound(residuals, p0, bounds, args=(y, x), maxfev=5000)  # Calculate the fit with Levenberg-Marquardt
    pfinal = plsq[0]  # final parameters
    # covar = plsq[1]  # covariance matrix

    # Calculate the output parameters
    # FWHM = sqrt(8*log(2)) * Gaussian_Sigma
    FWHM1 = 2.354820045 * pfinal[1]  # Full Width at Half Maximum for the first Gaussian
    FWHM2 = 2.354820045 * pfinal[3]  # Full Width at Half Maximum for the second Gaussian
    # Scale from cm to mm according to Gheorghe from Marburg
    FWHM1 *= 10.0
    FWHM2 *= 10.0
    # Get the amplitudes of the normalized form of the double Gaussian /TPR
    A1 = pfinal[0] * 2 * math.pi * FWHM1**2
    A2 = pfinal[2] * 2 * math.pi * FWHM2**2
    normfactor = A1 + A2  # changed to use of the normalized amplitudes /TPR
    if normfactor == 0:  # check if denominator is 0
        #        factor = 1.0
        print("normfactor = ", normfactor, energy, depth)
        factor = -1e6  # Calculate the factor between the two amplitudes
        # TODO: CHECK THAT THIS IS THE RIGHT ->#what's going on here?!?! /TPR
    else:
        factor = A2 / normfactor  # Calculate the factor between the two normalized amplitudes: factor = A2 / (A1+A2),
        # This definition was given by Gheorghe and Uli from Marburg!

    return FWHM1, factor, FWHM2


class TripDddWriter(object):

    _ddd_header_template = """!filetype    ddd
!fileversion   {fileversion:s}
!filedate      {filedate:s}
!projectile    {projectile:s}
!material      {material:s}
!composition   {composition:s}
!density {density:f}
!energy {energy:f}
#   z[g/cm**2] dE/dz[MeV/(g/cm**2)] FWHM1[mm] factor FWHM2[mm]
!ddd
"""

    def __init__(self, filename, options):
        self.ddd_filename = filename
        self.energy = options.energy
        self.ngauss = options.ngauss
        if not self.ddd_filename.endswith(".ddd"):
            self.ddd_filename += ".ddd"

    def _extract_data(self, detector):
        self.r_data_1d = np.asarray(list(detector.x)[0:detector.nx])
        self.z_data_1d = np.asarray(list(detector.z)[0:detector.nz * detector.nx:detector.nx])
        self.dose_data_2d = np.array(detector.v).reshape(detector.nz, detector.nx)
        self.dose_data_1d = np.sum(self.dose_data_2d, axis=1)

    def write(self, detector):
        from pymchelper.shieldhit.detector.detector_type import SHDetType

        if detector.dettyp == SHDetType.ddd:
            # time format: %c  Locale's appropriate date and time representation.
            now = time.strftime('%c')

            header = self._ddd_header_template.format(
                fileversion='19980520',
                filedate=now,
                projectile='C',
                material='H20',
                composition='H20',
                density=1,
                energy=self.energy)

            self._extract_data(detector)

            fwhm1_data = []
            fwhm2_data = []
            weight_data = []

            print("fitting...")

            if self.ngauss == 2:

                cumsum = np.cumsum(self.dose_data_1d)
                cumsum /= np.sum(self.dose_data_1d)

                cumsum_gr = np.array(cumsum)
                cumsum *= -1.0
                cumsum += 1.0

                threshold = 1e-4

                thr_ind = cumsum.size - np.searchsorted(cumsum[::-1], threshold) - 1
                z_fitting = self.z_data_1d[:thr_ind]

                for z, dose_at_z in zip(z_fitting, self.dose_data_2d[:thr_ind]):
                    r_fitting = self.r_data_1d[dose_at_z > 0]
                    dose_fitting = dose_at_z[dose_at_z > 0]

                    radial_dose = dose_fitting * r_fitting
                    fitParameters = _lateral_fit(r_fitting, radial_dose, z, 70)
                    fwhm1, factor, fwhm2 = fitParameters
                    fwhm1_data.append(fwhm1)
                    fwhm2_data.append(fwhm2)
                    weight_data.append(factor)

            print("writing...")
            with open(self.ddd_filename, 'w') as ddd_file:
                ddd_file.write(header)
                for e, fwhm1, weight, fwhm2 in zip(weight_data, fwhm1_data, weight_data, fwhm2_data):
                    ddd_file.write('??? {:g} {:g} {:g}\n'.format(fwhm1, weight, fwhm2))

            print("plotting...")
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            plt.plot(z_fitting, fwhm1_data, 'r')
            plt.xlabel('z [g/cm**2]')
            plt.ylabel('FWHM1 [g/cm**2]')
            plt.savefig('ddd_fwhm1.png')
            plt.close()

            plt.plot(z_fitting, fwhm2_data, 'g')
            plt.xlabel('z [g/cm**2]')
            plt.ylabel('FWHM2 [g/cm**2]')
            plt.savefig('ddd_fwhm2.png')
            plt.close()

            plt.plot(z_fitting, weight_data, 'b')
            plt.xlabel('z [g/cm**2]')
            plt.ylabel('weight')
            plt.savefig('ddd_weight.png')
            plt.close()

            plt.plot(z_fitting, self.dose_data_1d[0:thr_ind], 'b')
            plt.xlabel('z [g/cm**2]')
            plt.ylabel('dose')
            plt.savefig('ddd_dose.png')
            plt.close()

            plt.semilogy(z_fitting, self.dose_data_1d[0:thr_ind], 'b')
            plt.xlabel('z [g/cm**2]')
            plt.ylabel('dose')
            plt.savefig('ddd_dose_log.png')
            plt.close()

            plt.plot(self.z_data_1d, self.dose_data_1d, 'b')
            plt.xlabel('z [g/cm**2]')
            plt.ylabel('dose')
            plt.savefig('ddd_dose_all.png')
            plt.close()

            plt.semilogy(self.z_data_1d, self.dose_data_1d, 'b')
            plt.xlabel('z [g/cm**2]')
            plt.ylabel('dose')
            plt.savefig('ddd_dose_all_log.png')
            plt.close()

            plt.semilogy(self.z_data_1d, cumsum, 'b')
            plt.xlabel('z [g/cm**2]')
            plt.ylabel('dose')
            plt.axhline(y=threshold)
            plt.savefig('ddd_cs1.png')
            plt.close()

            plt.plot(self.z_data_1d, cumsum, 'b')
            plt.xlabel('z [g/cm**2]')
            plt.ylabel('dose')
            plt.savefig('ddd_cs2.png')
            plt.close()

            plt.plot(self.z_data_1d, cumsum_gr, 'b')
            plt.xlabel('z [g/cm**2]')
            plt.ylabel('dose')
            plt.savefig('ddd_cs_gr.png')
            plt.close()
