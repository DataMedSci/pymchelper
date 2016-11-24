import time
import logging
import math
import os
from copy import deepcopy

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

        import matplotlib
        matplotlib.use('Agg')
        self.ddd_filename = filename
        self.energy_MeV = options.energy
        self.ngauss = options.ngauss
        self.verbosity = options.verbose
        if not self.ddd_filename.endswith(".ddd"):
            self.ddd_filename += ".ddd"
        self.outputdir = os.path.abspath(os.path.dirname(self.ddd_filename))

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
                energy=self.energy_MeV)

            self._extract_data(detector)

            fwhm1_cm_data = []
            fwhm2_cm_data = []
            weight_data = []

            threshold = 3e-4

            cum_dose = self._cumulative_dose()
            cum_dose_left = self._cumulative_dose_left(cum_dose)

            thr_ind = cum_dose_left.size - np.searchsorted(cum_dose_left[::-1], threshold) - 1
            z_fitting_cm_1d = self.z_data_cm_1d[:thr_ind]
            dose_fitting_MeV_g_1d = self.dose_data_MeV_g_1d[:thr_ind]

            r_fitting_cm_2d, z_fitting_cm_2d = np.meshgrid(self.r_data_cm_1d, z_fitting_cm_1d)
            dose_fitting_MeV_g_2d = self.dose_data_MeV_g_2d[0:thr_ind]

            logger.info("Plotting 1..")
            if self.verbosity > 0:
                self._pre_fitting_plots(
                    cum_dose_left=cum_dose_left,
                    z_fitting_cm_1d=z_fitting_cm_1d,
                    dose_fitting_MeV_g_1d=dose_fitting_MeV_g_1d,
                    threshold=threshold,
                    zmax_cm=z_fitting_cm_1d[-1])

                self._plot_2d_map(z_fitting_cm_2d, r_fitting_cm_2d, dose_fitting_MeV_g_2d, z_fitting_cm_1d, None, None)

            logger.info("Fitting...")
            if self.ngauss in (1, 2):
                for z_cm, dose_at_z in zip(z_fitting_cm_1d, self.dose_data_MeV_g_2d[:thr_ind]):
                    r_fitting_cm = self.r_data_cm_1d[dose_at_z > 0]
                    dose_fitting_1d_positive_MeV_g = dose_at_z[dose_at_z > 0]

                    radial_dose_MeV_cm_g = dose_fitting_1d_positive_MeV_g * r_fitting_cm
                    fitParameters = self._lateral_fit(r_fitting_cm, radial_dose_MeV_cm_g, z_cm, self.energy_MeV,
                                                      self.ngauss)
                    fwhm1_cm, factor, fwhm2_cm = fitParameters
                    fwhm1_cm_data.append(fwhm1_cm)
                    fwhm2_cm_data.append(fwhm2_cm)  # set to 0 in case ngauss = 1
                    weight_data.append(factor)  # set to 0 in case ngauss = 1

            logger.info("Plotting 2...")
            if self.verbosity > 0 and self.ngauss in (1, 2):
                self._post_fitting_plots(z_fitting_cm_1d, fwhm1_cm_data, fwhm2_cm_data, weight_data)
                self._plot_2d_map(
                    z_fitting_cm_2d,
                    r_fitting_cm_2d,
                    dose_fitting_MeV_g_2d,
                    z_fitting_cm_1d,
                    fwhm1_cm_data,
                    fwhm2_cm_data,
                    suffix='_fwhm')

            logger.info("Writing " + self.ddd_filename)
            with open(self.ddd_filename, 'w') as ddd_file:
                ddd_file.write(header)
                if self.ngauss == 2:
                    for z_cm, dose, fwhm1_cm, weight, fwhm2_cm in zip(z_fitting_cm_1d, dose_fitting_MeV_g_1d,
                                                                      fwhm1_cm_data, weight_data, fwhm2_cm_data):
                        ddd_file.write('{:g} {:g} {:g} {:g} {:g}\n'.format(z_cm, dose, fwhm1_cm, weight, fwhm2_cm))
                elif self.ngauss == 1:
                    for z_cm, dose, fwhm_cm in zip(z_fitting_cm_1d, dose_fitting_MeV_g_1d, fwhm1_cm_data):
                        ddd_file.write('{:g} {:g} {:g}\n'.format(z_cm, dose, fwhm_cm))
                elif self.ngauss == 0:
                    for z_cm, dose in zip(z_fitting_cm_1d, dose_fitting_MeV_g_1d):
                        ddd_file.write('{:g} {:g}\n'.format(z_cm, dose))

    def _extract_data(self, detector):
        # 2D arrays of r,z and dose
        self.r_data_cm_2d = np.array(list(detector.x)).reshape(detector.nz, detector.nx)
        self.z_data_cm_2d = np.array(list(detector.z)).reshape(detector.nz, detector.nx)
        self.dose_data_MeV_g_2d = np.array(detector.v).reshape(detector.nz, detector.nx)

        # 1D arrays of r,z and dose in the very central bin
        self.r_data_cm_1d = self.r_data_cm_2d[0]
        self.z_data_cm_1d = np.asarray(list(detector.z)[0:detector.nz * detector.nx:detector.nx])
        self.dose_data_MeV_g_1d = self.dose_data_MeV_g_2d[:, 0]

    def _cumulative_dose(self):
        cumsum = np.cumsum(self.dose_data_MeV_g_1d)
        cumsum /= np.sum(self.dose_data_MeV_g_1d)
        return cumsum

    def _cumulative_dose_left(self, cumsum):
        cum_dose_left = np.array(cumsum)
        cum_dose_left *= -1.0
        cum_dose_left += 1.0
        return cum_dose_left

    def _plot_2d_map(self,
                     z_fitting_cm_2d,
                     r_fitting_cm_2d,
                     dose_fitting_MeV_g2d,
                     z_fitting_cm_1d=None,
                     fwhm1_cm=None,
                     fwhm2_cm=None,
                     suffix=''):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.colors import LogNorm

        prefix = os.path.join(self.outputdir, 'ddd_{:3.1f}MeV_'.format(self.energy_MeV))
        plt.pcolormesh(
            z_fitting_cm_2d, r_fitting_cm_2d, dose_fitting_MeV_g2d, norm=LogNorm(), cmap='gnuplot2', label='dose')
        cbar = plt.colorbar()
        cbar.set_label("dose [MeV/g]", rotation=270, verticalalignment='bottom')
        if z_fitting_cm_1d is not None and fwhm1_cm is not None:
            plt.plot(z_fitting_cm_1d, fwhm1_cm, label="fwhm1")
        if z_fitting_cm_1d is not None and fwhm2_cm is not None:
            plt.plot(z_fitting_cm_1d, fwhm2_cm, label="fwhm2")

        # plot legend only if some of the FWHM 1-D overlays are present
        # adding legend to only pcolormesh plot will result in a warning about missing labels
        if z_fitting_cm_1d is not None and (fwhm1_cm is not None or fwhm2_cm is not None):
            plt.legend(loc=0)
        plt.xlabel("z [cm]")
        plt.ylabel("r [cm]")
        plt.xlim((z_fitting_cm_2d.min(), z_fitting_cm_2d.max()))
        if fwhm1_cm is not None and fwhm2_cm is not None:
            plt.ylim((r_fitting_cm_2d.min(), max(max(fwhm1_cm), max(fwhm2_cm))))
        plt.clim((1e-8 * dose_fitting_MeV_g2d.max(), dose_fitting_MeV_g2d.max()))
        out_filename = prefix + 'dosemap' + suffix + '.png'
        logger.info('Saving ' + out_filename)
        plt.savefig(out_filename)
        if self.verbosity > 1:
            plt.yscale('log')
            out_filename = prefix + 'dosemap_log' + suffix + '.png'
            logger.info('Saving ' + out_filename)
            plt.savefig(out_filename)
        plt.close()

    def _pre_fitting_plots(self, cum_dose_left, z_fitting_cm_1d, dose_fitting_MeV_g_1d, threshold, zmax_cm):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        prefix = os.path.join(self.outputdir, 'ddd_{:3.1f}MeV_'.format(self.energy_MeV))

        plt.plot(self.z_data_cm_1d, self.dose_data_MeV_g_1d, color='blue', label='dose')
        plt.axvspan(
            0,
            zmax_cm,
            alpha=0.1,
            color='green',
            label="fitting area, covers {:g} % of dose".format(100.0 * (1 - threshold)))
        plt.legend(loc=0)
        plt.xlabel('z [cm]')
        plt.ylabel('dose [a.u.]')
        if self.verbosity > 1:
            out_filename = prefix + 'dose_all.png'
            logger.info('Saving ' + out_filename)
            plt.savefig(out_filename)
        plt.yscale('log')
        out_filename = prefix + 'all_log.png'
        logger.info('Saving ' + out_filename)
        plt.savefig(out_filename)
        plt.close()

        if self.verbosity > 1:
            bp_max_z_pos_cm = self.z_data_cm_1d[self.dose_data_MeV_g_1d == self.dose_data_MeV_g_1d.max()]

            plt.semilogy(self.z_data_cm_1d, cum_dose_left, color='blue', label="cumulative missing dose")
            plt.axvspan(
                0,
                zmax_cm,
                alpha=0.1,
                color='green',
                label="fitting area, covers {:g} % of dose".format(100.0 * (1 - threshold)))
            plt.axhline(threshold, color='black', label='threshold {:g}'.format(threshold))
            plt.axvline(bp_max_z_pos_cm, color='red', label='BP max')
            plt.legend(loc=0)
            plt.xlabel('z [cm]')
            plt.ylabel('fraction of total dose deposited behind z')
            out_filename = prefix + 'dose_frac.png'
            logger.info('Saving ' + out_filename)
            plt.savefig(out_filename)
            plt.close()

        plt.plot(z_fitting_cm_1d, dose_fitting_MeV_g_1d, 'b', label='dose')
        plt.xlabel('z [cm]')
        plt.ylabel('dose [MeV/g]')
        out_filename = prefix + 'dose.png'
        logger.info('Saving ' + out_filename)
        plt.savefig(out_filename)
        if self.verbosity > 1:
            plt.yscale('log')
            out_filename = prefix + 'dose_log.png'
            logger.info('Saving ' + out_filename)
            plt.savefig(out_filename)
        plt.close()

    def _post_fitting_plots(self, z_fitting_1d, fwhm1_cm_data, fwhm2_cm_data, weight_data):
        import matplotlib.pyplot as plt
        prefix = os.path.join(self.outputdir, 'ddd_{:3.1f}MeV_'.format(self.energy_MeV))

        # left Y axis dedicated to FWHM, right one to weight
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        lns1 = ax1.plot(z_fitting_1d, fwhm1_cm_data, 'r', label='fwhm1')
        if fwhm2_cm_data is not None:
            lns2 = ax1.plot(z_fitting_1d, fwhm2_cm_data, 'g', label='fwhm2')
        if weight_data is not None:
            lns3 = ax2.plot(z_fitting_1d, weight_data, 'b', label='weight')
            ax2.set_ylabel('weight of FWHM1')
        ax1.set_xlabel('z [cm]')
        ax1.set_ylabel('FWHM [cm]')

        # add by hand line plots and labels to legend
        line_objs = lns1
        if fwhm2_cm_data is not None:
            line_objs += lns2
        if weight_data is not None:
            line_objs += lns3
        labels = [l.get_label() for l in line_objs]
        ax1.legend(line_objs, labels, loc=0)

        out_filename = prefix + 'fwhm.png'
        logger.info('Saving ' + out_filename)
        plt.savefig(out_filename)
        plt.close()

    @staticmethod
    def _lateral_fit(left_radii_cm, radial_dose_scaled, depth_cm, energy_MeV, ngauss=2):
        """
        Fitting for lateral dose distribution
        Fits the lateral dose scaled with the radius using a double Gaussian by the use of Levenberg-Marquardt alg.
        Parameters:
        * radii        radius values corresponding to dose
        * dose         dose D(r)
        * dose_scaled  dose times the radii D(r)*r
        * depth        only used for graphing
        * energy       only used for graphing

        Returns: (x,{cov_x,infodict,mesg},ier)
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
            from scipy.optimize import leastsq

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

        def residuals_1g(p, y, x):  # objective function for minimization (vector function)
            err = y - peval_1g(x, mu, p)
            return err

        def residuals_2g(p, y, x):  # objective function for minimization (vector function)
            err = y - peval_2g(x, mu, p)
            return err

        def peval_1g(x, mu, p):  # The model function: One gaussian
            return p[0] * np.exp(-((x - mu)**2) / (2 * p[1]**2)) * x

        def peval_2g(x_cm, mu_cm, p):  # The model function: Two gaussians (sum), the mean mu is locked
            # In guideline with a similar routine for TRiP by U. Weber,
            # the function is scaled with the radius to fit D(r)*r /TPR
            return (p[0] * np.exp(-((x_cm - mu_cm)**2) / (2 * p[1]**2)) + p[2] * np.exp(-(
                (x_cm - mu_cm)**2) / (2 * p[3]**2))) * x_cm

        x = left_radii_cm
        y = radial_dose_scaled
        # Calculate initial guesses #
        a1 = y.max()  # guess for the amplitude of the first gaussian
        mu = 0  # set the mean to zero - a guess would be: sum(x*y)/sum(y)
        if sum(y) == 0:  # check if denominator is 0
            sigma1 = 1e5
        else:
            sigma1 = np.sqrt(abs(sum((x - mu)**2 * y) / sum(y)))  # guess for the deviation

        if ngauss == 2:
            a2 = deepcopy(a1) * 0.05  # guess for the  amplitude of the second gaussian
            sigma2 = 2  # guess for the deviation of the second gaussian
            sigma2 = deepcopy(sigma1) * 5.0
            # Collect the guesses in an array
            p0 = np.asarray([a1, sigma1, a2, sigma2])
            bounds = [(0, 1e6), (0, 1e6), (0, 1e6), (0, 1e6)]  # set bound for the parameters,
            # they should be non-negative
            plsq = leastsqbound(residuals_2g, p0, bounds, args=(y, x), maxfev=5000)  # Calculate the fit
        elif ngauss == 1:
            # Collect the guesses in an array
            p0 = np.asarray([a1, sigma1])
            bounds = [(0, 1e6), (0, 1e6)]  # set bound for the parameters, they should be non-negative
            plsq = leastsqbound(residuals_1g, p0, bounds, args=(y, x), maxfev=5000)  # Calculate the fit

        pfinal = plsq[0]  # final parameters
        # covar = plsq[1]  # covariance matrix

        # Calculate the output parameters
        # FWHM = sqrt(8*log(2)) * Gaussian_Sigma
        fwhm1 = 2.354820045 * pfinal[1]  # Full Width at Half Maximum for the first Gaussian
        if ngauss == 2:
            fwhm2 = 2.354820045 * pfinal[3]  # Full Width at Half Maximum for the second Gaussian
            A2 = pfinal[2] * 2 * math.pi * fwhm2**2
        else:
            fwhm2 = 0.0
            A2 = 0.0
        # Scale from cm to mm according to Gheorghe from Marburg
        # fwhm1 *= 10.0
        # fwhm2 *= 10.0
        # Get the amplitudes of the normalized form of the double Gaussian
        A1 = pfinal[0] * 2 * math.pi * fwhm1**2
        normfactor = A1 + A2  # changed to use of the normalized amplitudes
        if normfactor == 0:  # check if denominator is 0
            #        factor = 1.0
            logger.debug("normfactor = " + normfactor + " , energy = " + energy_MeV + " , depth = " + depth_cm)
            factor = -1e6  # Calculate the factor between the two amplitudes
            # TODO: CHECK THAT THIS IS THE RIGHT ->#what's going on here?!?!
        else:
            factor = A2 / normfactor
            # Calculate the factor between the two normalized amplitudes: factor = A2 / (A1+A2),
            # This definition was given by Gheorghe and Uli from Marburg!

        return fwhm1, factor, fwhm2
