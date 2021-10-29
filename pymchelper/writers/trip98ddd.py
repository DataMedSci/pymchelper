import logging
import math
import os
import time
import numpy as np

logger = logging.getLogger(__name__)


class TRiP98DDDWriter(object):
    """
    Writer for TRiP98 DDD files. File format is described here:
    http://bio.gsi.de/DOCS/TRiP98/PRO/DOCS/trip98fmtddd.html

    Only liquid water target is supported now.


    """

    _suffix_template = '{projectile:s}.{material:s}.{unit:s}{energy:s}'

    _ddd_header_template = """!filetype    ddd
!fileversion   {fileversion:s}
!filedate      {filedate:s}
!projectile    {projectile:s}
!material      {material:s}
!composition   {composition:s}
!density {density:f}
!energy {energy:f}
#
# {creator:s}
#
#   z[g/cm**2] dE/dz[MeV/(g/cm**2)] FWHM1[g/cm**2] factor FWHM2[g/cm**2]
!ddd
"""

    def __init__(self, filename, options):
        self.ddd_filename = filename
        self.energy_MeV_u = options.energy  # energy in MeV/u
        self.projectile = options.projectile  # projectile code, i.e. 1H, 12C
        self.suffix = ''
        self.ngauss = options.ngauss
        self.verbosity = options.verbose
        if not self.ddd_filename.endswith(".ddd"):
            self.ddd_filename += ".ddd"
        self.outputdir = os.path.abspath(os.path.dirname(self.ddd_filename))
        self.threshold = 3e-3
        env_var_name = 'DDD_TAIL_THRESHOLD'
        if env_var_name in os.environ:
            self.threshold = float(os.environ[env_var_name])
            logger.info("Setting tail threshold based on {:s} to {:f}".format(env_var_name, self.threshold))

    def write(self, estimator):

        # guess projectile and energy from MC data
        if self.projectile is None:
            try:
                element_names = ['n', 'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si',
                                 'P', 'S', 'Cl', 'Ar', 'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu',
                                 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc',
                                 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La',
                                 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu',
                                 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At',
                                 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es',
                                 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn', 'Nh',
                                 'Fl', 'Mc', 'Lv', 'Ts', 'Og']
                self.projectile = "{:d}{:s}".format(
                    int(estimator.projectile_a),
                    element_names[int(estimator.projectile_z)],
                )
            except AttributeError:
                self.projectile = ''
                logger.error('Projectile not available in raw data, setting to empty string')

        if self.energy_MeV_u is None:
            try:
                self.energy_MeV_u = getattr(estimator, 'Tmax_MeV/amu')
            except AttributeError:
                self.energy_MeV_u = 0.0
                logger.error('Projectile energy not available in raw data, setting to 0')

        #     The usual naming convention is <pp>.<tt>.<uuu><eeeee>.ddd, where <pp> denotes the projectile,
        #     <tt> the target material, <uuu> the unit (keV, MeV, GeV) and <eeeee> the energy in these units,
        #     with the decimal point after the middle digit. Example: 12C.H2O.MeV27000.spc refers to 270 MeV/u.
        self.suffix = self._suffix_template.format(projectile=self.projectile, material='H2O', unit='MeV',
                                                   energy=str(int(self.energy_MeV_u * 100)).zfill(5))

        # save to single page to a file without number (i.e. output.ddd)
        if len(estimator.pages) == 1:
            self.write_single_page(estimator, estimator.pages[0], self.ddd_filename)
        else:

            # split output path into directory, basename and extension
            dir_path = os.path.dirname(self.ddd_filename)
            if not os.path.exists(dir_path):
                logger.info("Creating {}".format(dir_path))
                os.makedirs(dir_path)
            file_base_part, file_ext = os.path.splitext(os.path.basename(self.ddd_filename))

            # loop over all pages and save an image for each of them
            for i, page in enumerate(estimator.pages):

                # calculate output filename. it will include page number padded with zeros.
                # for 10-99 pages the filename would look like: output_p01.ddd, ... output_p99.ddd
                # for 100-999 pages the filename would look like: output_p001.ddd, ... output_p999.ddd
                zero_padded_page_no = str(i + 1).zfill(len(str(len(estimator.pages))))
                output_filename = "{}_p{}{}".format(file_base_part, zero_padded_page_no, file_ext)
                output_path = os.path.join(dir_path, output_filename)

                # save the output file
                logger.info("Writing {}".format(output_path))
                self.write_single_page(estimator, page, output_path)

        return 0

    def write_single_page(self, estimator, page, filename):

        logger.info("Writing {:s}".format(filename))

        from pymchelper.shieldhit.detector.detector_type import SHDetType
        if page.dettyp != SHDetType.ddd:
            logger.warning("Incompatible estimator {:s} used, use {:s} instead".format(page.dettyp, SHDetType.ddd))
            return 1

        # extract data from detector data
        data = self._extract_data(estimator, page)

        # in order to avoid fitting data to noisy region far behind Bragg peak tail,
        # find the range of z coordinate which contains (1-threshold) of the deposited energy
        cum_dose = LateralDepthDoseProfile.cumulative_dose(data.dose_MeV_g_1d)
        cum_dose_left = LateralDepthDoseProfile.cumulative_dose_left(cum_dose)

        thr_ind = cum_dose_left.size - np.searchsorted(cum_dose_left[::-1], self.threshold) - 1
        z_fitting_cm_1d = data.z_cm_1d[:thr_ind]
        dose_fitting_MeV_g_1d = data.dose_MeV_g_1d[:thr_ind]

        # r_fitting_cm_2d, z_fitting_cm_2d = np.meshgrid(data.r_cm_1d, z_fitting_cm_1d)
        # dose_fitting_MeV_g_2d = data.dose_MeV_g_2d[0:thr_ind]

        if self.verbosity > 0:
            logger.info("Plotting base data..")

            fig = DebuggingPlots(data).base_data(zmax_cm=z_fitting_cm_1d[-1], threshold=self.threshold)
            fig_filename = "{:s}_depth_dose.png".format(os.path.splitext(filename)[0])
            logger.info("Writing {:s}".format(fig_filename))
            fig.savefig(fig_filename)

            fig = DebuggingPlots(data).base_data(zmax_cm=z_fitting_cm_1d[-1], threshold=self.threshold, logy=True)
            fig_filename = "{:s}_depth_dose_log.png".format(os.path.splitext(filename)[0])
            logger.info("Writing {:s}".format(fig_filename))
            fig.savefig(fig_filename)

            if self.ngauss in (1, 2):
                fig = DebuggingPlots(data).map2d()
                fig_filename = "{:s}_dose_map.png".format(os.path.splitext(filename)[0])
                logger.info("Writing {:s}".format(fig_filename))
                fig.savefig(fig_filename)

                fig = DebuggingPlots(data).map2d(zlog=True)
                fig_filename = "{:s}_dose_map_log.png".format(os.path.splitext(filename)[0])
                logger.info("Writing {:s}".format(fig_filename))
                fig.savefig(fig_filename)

        fit_results = FitResultCollection(z_fitting_cm_1d.size)
        if self.ngauss in (1, 2):
            logger.info("Fitting...")

            if data.r_cm_1d.size < 10:
                logger.warning("Number of bins in R dimension is {:d} and is lower than 10.".format(data.r_cm_1d.size))
                return 1

            # for each depth fit a lateral beam with gaussian models
            for ind, z_cm in enumerate(z_fitting_cm_1d):

                dose_at_z = data.dose_MeV_g_2d[ind]

                # take into account only this position in r for which dose is positive
                r_fitting_cm = data.r_cm_1d[dose_at_z > 0]
                dose_fitting_1d_positive_MeV_g = dose_at_z[dose_at_z > 0]

                # perform the fit
                params, params_error = self._lateral_fit(r_fitting_cm,
                                                         dose_fitting_1d_positive_MeV_g,
                                                         self.ngauss)

                if params is None and params_error is None:  # fitting failed, i.e. due to missing scipy
                    return 1

                fwhm1_cm, factor, fwhm2_cm, dz0_MeV_cm_g = params
                fwhm1_cm_error, factor_error, fwhm2_cm_error, dz0_MeV_cm_g_error = params_error

                fit_results.z_cm[ind] = z_cm

                fit_results.data['fwhm1_cm'][ind] = fwhm1_cm
                fit_results.error['fwhm1_cm'][ind] = fwhm1_cm_error

                fit_results.data['dz0_MeV_cm_g'][ind] = dz0_MeV_cm_g
                fit_results.error['dz0_MeV_cm_g'][ind] = dz0_MeV_cm_g_error

                if self.ngauss == 2:
                    fit_results.data['fwhm2_cm'][ind] = fwhm2_cm
                    fit_results.error['fwhm2_cm'][ind] = fwhm2_cm_error

                    fit_results.data['factor'][ind] = factor
                    fit_results.error['factor'][ind] = factor_error

        if self.verbosity > 0 and self.ngauss in (1, 2):
            logger.info("Plotting fitting results...")

            fig = DebuggingPlots(data).fit_summary(
                fit_results
            )
            fig_filename = "{:s}_fitting.png".format(os.path.splitext(filename)[0])
            logger.info("Writing {:s}".format(fig_filename))
            fig.savefig(fig_filename)

        logger.info("Writing " + filename)

        from pymchelper import __version__ as _pmcversion
        _creator_info = "Created with pymchelper {:s}".format(_pmcversion)

        # prepare header of DDD file
        header = self._ddd_header_template.format(
            fileversion='19980520',
            filedate=time.strftime('%c'),  # Locale's appropriate date and time representation
            projectile=self.projectile,
            material='H2O',
            composition='H2O',
            density=1,
            creator=_creator_info,
            energy=self.energy_MeV_u)

        filename_with_suffix = os.path.splitext(filename)[0]
        filename_with_suffix += '_'
        filename_with_suffix += self.suffix
        filename_with_suffix += '.ddd'
        logger.info("Saving {:s}".format(filename_with_suffix))

        # write the contents of the files
        with open(filename_with_suffix, 'w') as ddd_file:
            ddd_file.write(header)
            # TODO write to DDD gaussian amplitude, not the dose in central bin
            if self.ngauss == 2:
                for z_cm, dose, fwhm1_cm, weight, fwhm2_cm in zip(z_fitting_cm_1d,
                                                                  dose_fitting_MeV_g_1d,
                                                                  fit_results.data['fwhm1_cm'],
                                                                  fit_results.data['factor'],
                                                                  fit_results.data['fwhm2_cm']):
                    ddd_file.write('{:g} {:g} {:g} {:g} {:g}\n'.format(z_cm, dose, fwhm1_cm, weight, fwhm2_cm))
            elif self.ngauss == 1:
                for z_cm, dose, fwhm_cm in zip(z_fitting_cm_1d, dose_fitting_MeV_g_1d, fit_results.data['fwhm1_cm']):
                    ddd_file.write('{:g} {:g} {:g}\n'.format(z_cm, dose, fwhm_cm))
            elif self.ngauss == 0:
                for z_cm, dose in zip(z_fitting_cm_1d, dose_fitting_MeV_g_1d):
                    ddd_file.write('{:g} {:g}\n'.format(z_cm, dose))

        return 0

    @classmethod
    def _extract_data(cls, estimator, page):
        if estimator.x.n > 1:
            r_step_cm = estimator.x.data[1] - estimator.x.data[0]
        else:
            r_step_cm = estimator.x.max_val

        if estimator.z.n > 1:
            z_step_cm = estimator.z.data[1] - estimator.z.data[0]
        else:
            z_step_cm = estimator.z.max_val

        data = LateralDepthDoseProfile(r_cm_1d=estimator.x.data,
                                       z_cm_1d=estimator.z.data,
                                       dose_MeV_g_2d=page.data_raw.reshape((estimator.z.n, estimator.x.n)),
                                       dose_error_MeV_g_2d=page.error_raw.reshape((estimator.z.n, estimator.x.n)),
                                       r_step_cm=r_step_cm,
                                       z_step_cm=z_step_cm)

        return data

    @classmethod
    def _lateral_fit(cls, r_cm, dose_MeV_g, ngauss=1):
        variance = np.average(r_cm ** 2, weights=dose_MeV_g)

        start_amp_MeV_g = dose_MeV_g.max()
        start_sigma_cm = np.sqrt(variance)

        min_amp_MeV_g = 1e-10 * dose_MeV_g.max()
        min_sigma_cm = 1e-2 * start_sigma_cm

        max_amp_MeV_g = 2.0 * dose_MeV_g.max()
        max_sigma_cm = 1e4 * start_sigma_cm

        try:
            from scipy.optimize import curve_fit
        except ImportError:
            logger.error("scipy package missing, to install type `pip install scipy`")
            return None, None

        if ngauss == 1:
            try:
                popt, pcov = curve_fit(f=FittingMethods.gauss_r_MeV_cm_g,
                                       xdata=r_cm,
                                       ydata=dose_MeV_g * r_cm,
                                       p0=[start_amp_MeV_g, start_sigma_cm],
                                       bounds=([[min_amp_MeV_g, min_sigma_cm], [max_amp_MeV_g, max_sigma_cm]]),
                                       sigma=None)
                # TODO return also parameter errors
                perr = np.sqrt(np.diag(pcov))

                dz0_MeV_cm_g, sigma_cm = popt
                dz0_MeV_cm_g_error, sigma_cm_error = perr
            except RuntimeError as e:
                logger.warning(e)
                dz0_MeV_cm_g, sigma_cm = np.nan, np.nan
                dz0_MeV_cm_g_error, sigma_cm_error = np.nan, np.nan
            factor = 0.0
            factor_error = 0.0
            fwhm2_cm = 0.0
            fwhm2_cm_error = 0.0

        elif ngauss == 2:
            start_weigth = 0.99
            start_sigma2_add_cm = 0.1

            min_weigth = 0.55
            min_sigma2_add_cm = 1e-1

            max_weigth = 1.0 - 1e-12
            max_sigma2_add_cm = 20.0

            try:
                popt, pcov = curve_fit(f=FittingMethods.gauss2_r_MeV_cm_g,
                                       xdata=r_cm,
                                       ydata=dose_MeV_g * r_cm,
                                       p0=[start_amp_MeV_g, start_sigma_cm, start_weigth, start_sigma2_add_cm],
                                       bounds=([min_amp_MeV_g, min_sigma_cm, min_weigth, min_sigma2_add_cm],
                                               [max_amp_MeV_g, max_sigma_cm, max_weigth, max_sigma2_add_cm]),
                                       sigma=None)
                perr = np.sqrt(np.diag(pcov))
                dz0_MeV_cm_g_error, sigma_cm_error, factor_error, sigma2_add_cm_error = perr
                dz0_MeV_cm_g, sigma_cm, factor, sigma2_add_cm = popt
            except RuntimeError as e:
                logger.warning(e)
                dz0_MeV_cm_g_error, sigma_cm_error, factor_error, sigma2_add_cm_error = np.nan, np.nan, np.nan, np.nan
                dz0_MeV_cm_g, sigma_cm, factor, sigma2_add_cm = np.nan, np.nan, np.nan, np.nan
            # TODO return also parameter errors
            sigma2_cm = sigma_cm + sigma2_add_cm
            sigma2_cm_error = (sigma_cm_error**2 + sigma2_add_cm_error**2)**0.5
            fwhm2_cm = sigma2_cm * FittingMethods._sigma_to_fwhm
            fwhm2_cm_error = sigma2_cm_error * FittingMethods._sigma_to_fwhm

        fwhm1_cm = sigma_cm * FittingMethods._sigma_to_fwhm

        fwhm1_cm_error = sigma_cm_error * FittingMethods._sigma_to_fwhm

        params = fwhm1_cm, factor, fwhm2_cm, dz0_MeV_cm_g
        params_error = fwhm1_cm_error, factor_error, fwhm2_cm_error, dz0_MeV_cm_g_error

        return params, params_error


class FitResultCollection(object):
    """
    Fit results collection (along Z axis)
    """
    def __init__(self, n):
        self.z_cm = np.zeros(shape=(n,))
        self.data = np.zeros(shape=(n,),
                             dtype=[('fwhm1_cm', 'double'),
                                    ('fwhm2_cm', 'double'),
                                    ('factor', 'double'),
                                    ('dz0_MeV_cm_g', 'double'),
                                    ]
                             )
        self.error = np.zeros(shape=(n,),
                              dtype=[('fwhm1_cm', 'double'),
                                     ('fwhm2_cm', 'double'),
                                     ('factor', 'double'),
                                     ('dz0_MeV_cm_g', 'double'),
                                     ]
                              )


class LateralDepthDoseProfile(object):
    """
    Base data for fitting
    """
    def __init__(self, r_cm_1d, z_cm_1d, dose_MeV_g_2d, dose_error_MeV_g_2d, r_step_cm=None, z_step_cm=None):
        # 1D arrays of r,z
        self.r_cm_1d = r_cm_1d
        self.z_cm_1d = z_cm_1d

        # 2D arrays of r,z, dose and error
        self.r_cm_2d, self.z_cm_2d = np.meshgrid(self.r_cm_1d, self.z_cm_1d)

        self.dose_MeV_g_2d = dose_MeV_g_2d
        self.dose_error_MeV_g_2d = dose_error_MeV_g_2d

        # dose in the very central bin
        if z_step_cm:
            bin_width_z_cm = z_step_cm
        elif self.z_cm_1d.size > 1:
            bin_width_z_cm = self.z_cm_1d[1] - self.z_cm_1d[0]
        else:
            raise Exception("Z depth step cannot be estimated")

        if r_step_cm:
            bin_width_r_cm = r_step_cm
        elif self.r_cm_1d.size > 1:
            bin_width_r_cm = self.r_cm_1d[1] - self.r_cm_1d[0]
        else:
            raise Exception("Z depth step cannot be estimated")

        # Bin volume increases as we move away from beam axis
        # i-th bin volume = dz * pi * (r_i_max^2 - r_i_min^2  )
        #   r_i_max = r_i + dr / 2
        #   r_i_min = r_i - dr / 2
        #  r_i_max^2 - r_i_min^2 = (r_i_max - r_i_min)*(r_i_max + r_i_min) = dr * 2 * r_i    thus
        # i-th bin volume = 2 * pi * dr * r_i * dz
        bin_volume_data_cm3_1d = 2.0 * np.pi * bin_width_r_cm * self.r_cm_1d * bin_width_z_cm
        # we assume density of 1 g/c3
        density_g_cm3 = 1.0
        energy_in_bin_MeV_2d = self.dose_MeV_g_2d * bin_volume_data_cm3_1d * density_g_cm3
        total_bin_mass_g = density_g_cm3 * bin_width_z_cm * np.pi * (self.r_cm_1d[-1] + bin_width_r_cm / 2.0) ** 2
        total_energy_at_depth_MeV_1d = np.sum(energy_in_bin_MeV_2d, axis=1)
        self.dose_MeV_g_1d = total_energy_at_depth_MeV_1d / total_bin_mass_g

    @staticmethod
    def cumulative_dose(dose_1d):
        cumsum = np.cumsum(dose_1d)
        cumsum /= np.sum(dose_1d)
        return cumsum

    @staticmethod
    def cumulative_dose_left(cumsum):
        cum_dose_left = np.array(cumsum)
        cum_dose_left *= -1.0
        cum_dose_left += 1.0
        return cum_dose_left


class FittingMethods(object):
    """
    Functions describing Gaussian functions modelling lateral dose distributions
    """

    _sigma_to_fwhm = 2. * (2. * math.log(2.)) ** 0.5

    @classmethod
    def gauss_MeV_g(cls, x_cm, amp_MeV_cm_g, sigma_cm):
        return amp_MeV_cm_g / (2.0 * np.pi * sigma_cm) * np.exp(-x_cm ** 2 / (2.0 * sigma_cm ** 2))

    @classmethod
    def gauss_r_MeV_cm_g(cls, x_cm, amp_MeV_cm_g, sigma_cm):
        return cls.gauss_MeV_g(x_cm, amp_MeV_cm_g, sigma_cm) * x_cm

    @classmethod
    def gauss2_MeV_g(cls, x_cm, amp_MeV_cm_g, sigma1_cm, weight, sigma2_add_cm):
        return amp_MeV_cm_g / (2.0 * np.pi) * (
            (weight / sigma1_cm) * np.exp(-x_cm ** 2 / (2.0 * sigma1_cm ** 2))
            + ((1.0 - weight) / (sigma1_cm + sigma2_add_cm))
            * np.exp(-x_cm ** 2 / (2.0 * (sigma1_cm + sigma2_add_cm) ** 2))
        )

    @classmethod
    def gauss2_MeV_g_1st(cls, x_cm, amp_MeV_cm_g, sigma1_cm, weight, sigma2_add_cm):
        return amp_MeV_cm_g / (2.0 * np.pi) * (weight / sigma1_cm) * np.exp(-x_cm ** 2 / (2.0 * sigma1_cm ** 2))

    @classmethod
    def gauss2_MeV_g_2nd(cls, x_cm, amp_MeV_cm_g, sigma1_cm, weight, sigma2_add_cm):
        return amp_MeV_cm_g / (2.0 * np.pi) * ((1.0 - weight) / (sigma1_cm + sigma2_add_cm)) * np.exp(
            -x_cm ** 2 / (2.0 * (sigma1_cm + sigma2_add_cm) ** 2))

    @classmethod
    def gauss2_r_MeV_cm_g(cls, x_cm, amp_MeV_cm_g, sigma1_cm, weight, sigma2_add_cm):
        return cls.gauss2_MeV_g(x_cm, amp_MeV_cm_g, sigma1_cm, weight, sigma2_add_cm) * x_cm


class DebuggingPlots(object):
    """
    Debugging plots, mostly needed to inspect if Gaussian function fitting was successful
    """
    def __init__(self, base_data):
        self.data = base_data

    def base_data(self, zmax_cm, threshold, logy=False):
        try:
            logging.getLogger('matplotlib').setLevel(logging.INFO)
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            # set matplotlib logging level to ERROR, in order not to pollute our log space
            logging.getLogger('matplotlib').setLevel(logging.ERROR)
        except ImportError:
            logger.error("Matplotlib not installed, output won't be generated")
            return 1
        fig, ax = plt.subplots()
        ax.plot(self.data.z_cm_1d, self.data.dose_MeV_g_1d, color='blue', label='dose')
        ax.axvspan(
            0,
            zmax_cm,
            alpha=0.1,
            color='green',
            label="fitting area, covers {:g} % of dose".format(100.0 * (1 - threshold)))
        ax.legend(loc=0)
        ax.set_xlabel('z [cm]')
        ax.set_ylabel('dose [MeV/g]')
        if logy:
            ax.set_yscale('log')
        return fig

    def map2d(self,
              zlog=False):
        try:
            logging.getLogger('matplotlib').setLevel(logging.INFO)
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib import colors
        except ImportError:
            logger.error("Matplotlib not installed, output won't be generated")
            return 1
        fig, ax = plt.subplots()
        # configure scale on Z axis
        if zlog:
            norm = colors.LogNorm(vmin=self.data.dose_MeV_g_2d[self.data.dose_MeV_g_2d > 0].min(),
                                  vmax=self.data.dose_MeV_g_2d.max())
        else:
            norm = colors.Normalize(vmin=self.data.dose_MeV_g_2d.min(),
                                    vmax=self.data.dose_MeV_g_2d.max())
        im = ax.pcolormesh(self.data.z_cm_2d, self.data.r_cm_2d, self.data.dose_MeV_g_2d,
                           norm=norm,
                           cmap='gnuplot2', label='dose')
        ax.set_xlabel("Z [cm]")
        ax.set_ylabel("R [cm]")
        cbar = fig.colorbar(im)
        cbar.set_label("dose [MeV/g]", rotation=270, verticalalignment='bottom')

        return fig

        # if z_fitting_cm_1d is not None and np.any(fwhm1_cm):
        #     plt.plot(z_fitting_cm_1d, fwhm1_cm, color='g', label="fwhm1")
        # if z_fitting_cm_1d is not None and np.any(fwhm2_cm):
        #     plt.plot(z_fitting_cm_1d, fwhm2_cm, color='r', label="fwhm2")

        # plot legend only if some of the FWHM 1-D overlays are present
        # adding legend to only pcolormesh plot will result in a warning about missing labels
        # if z_fitting_cm_1d is not None and (np.any(fwhm1_cm) or np.any(fwhm2_cm)):
        #     plt.legend(loc=0)
        # plt.xlabel("z [cm]")
        # plt.ylabel("r [cm]")
        # plt.xlim((z_fitting_cm_2d.min(), z_fitting_cm_2d.max()))
        # if np.any(fwhm1_cm) and np.any(fwhm2_cm):
        #     plt.ylim((r_fitting_cm_2d.min(), max(max(fwhm1_cm), max(fwhm2_cm))))
        # plt.clim((1e-8 * dose_fitting_MeV_g2d.max(), dose_fitting_MeV_g2d.max()))
        # out_filename = prefix + 'dosemap' + suffix + '.png'
        # logger.info('Saving ' + out_filename)
        # plt.savefig(out_filename)
        # if self.verbosity > 1:
        #     plt.yscale('log')
        #     out_filename = prefix + 'dosemap_log' + suffix + '.png'
        #     logger.info('Saving ' + out_filename)
        #     plt.savefig(out_filename)
        # plt.close()
        #
        # if self.verbosity > 2 and (np.any(fwhm1_cm) or np.any(fwhm2_cm)):
        #     # TODO add plotting sum of 2 gausses
        #
        #     sigma1_cm = fwhm1_cm / self._sigma_to_fwhm
        #     sigma2_cm = fwhm2_cm / self._sigma_to_fwhm
        #     gauss_amplitude_MeV_g = dz0_MeV_cm_g_data
        #     for z_cm, sigma1_at_z_cm, sigma2_at_z_cm, factor, amplitude_MeV_g in \
        #             zip(z_fitting_cm_1d, sigma1_cm, sigma2_cm, weight, gauss_amplitude_MeV_g):
        #         dose_mc_MeV_g = self.dose_data_MeV_g_2d[self.z_data_cm_2d == z_cm]
        #         title = "Z = {:4.3f} cm,  sigma1 = {:4.3f} cm".format(z_cm, sigma1_at_z_cm)
        #         plt.plot(self.r_data_cm_1d, dose_mc_MeV_g, 'k.', label="data")
        #         if self.ngauss == 1:
        #             gauss_data_MeV_g = self.gauss_MeV_g(self.r_data_cm_1d, amplitude_MeV_g, sigma1_at_z_cm)
        #             plt.plot(self.r_data_cm_1d, gauss_data_MeV_g, label="fit")
        #         elif self.ngauss == 2:
        #             gauss_data_MeV_g = self.gauss2_MeV_g(self.r_data_cm_1d, amplitude_MeV_g,
        #                                                  sigma1_at_z_cm, factor, sigma2_at_z_cm)
        #             gauss_data_MeV_g_1st = self.gauss2_MeV_g_1st(self.r_data_cm_1d, amplitude_MeV_g,
        #                                                          sigma1_at_z_cm, factor, sigma2_at_z_cm)
        #             gauss_data_MeV_g_2nd = self.gauss2_MeV_g_2nd(self.r_data_cm_1d, amplitude_MeV_g,
        #                                                          sigma1_at_z_cm, factor, sigma2_at_z_cm)
        #             plt.plot(self.r_data_cm_1d, gauss_data_MeV_g, label="fit")
        #             plt.plot(self.r_data_cm_1d, gauss_data_MeV_g_1st, label="fit 1st gauss")
        #             plt.plot(self.r_data_cm_1d, gauss_data_MeV_g_2nd, label="fit 2nd gauss")
        #             title += ", sigma2 = {:4.3f} cm, factor = {:4.6f}".format(sigma2_at_z_cm, factor)
        #         logger.debug("Plotting at " + title)
        #         plt.title(title)
        #         plt.legend(loc=0)
        #         plt.yscale('log')
        #         plt.xlabel("r [cm]")
        #         plt.ylabel("dose [MeV/g]")
        #         plt.ylim([dose_mc_MeV_g.min(), dose_mc_MeV_g.max()])
        #         if self.ngauss == 1:
        #             plt.ylim([dose_mc_MeV_g.min(), max(gauss_data_MeV_g.max(), dose_mc_MeV_g.max())])
        #         out_filename = prefix + "fit_details_{:4.3f}_log".format(z_cm) + suffix + '.png'
        #         logger.info('Saving ' + out_filename)
        #         plt.savefig(out_filename)
        #
        #         plt.xscale('log')
        #         plt.xlim([0, self.r_data_cm_1d.max()])
        #         out_filename = prefix + "fit_details_{:4.3f}_loglog".format(z_cm) + suffix + '.png'
        #         logger.info('Saving ' + out_filename)
        #         plt.savefig(out_filename)
        #
        #         plt.xscale('linear')
        #         plt.xlim([0, 5.0 * sigma2_at_z_cm])
        #         plt.ylim([dose_mc_MeV_g[self.r_data_cm_1d < 5.0 * sigma2_at_z_cm].min(), dose_mc_MeV_g.max()])
        #         out_filename = prefix + "fit_details_{:4.3f}_small_log".format(z_cm) + suffix + '.png'
        #         logger.info('Saving ' + out_filename)
        #         plt.savefig(out_filename)
        #
        #         plt.close()
        #
        #         plt.plot(self.r_data_cm_1d, dose_mc_MeV_g * self.r_data_cm_1d, 'k.', label="data")
        #         plt.plot(self.r_data_cm_1d, gauss_data_MeV_g * self.r_data_cm_1d, label="fit")
        #         plt.legend(loc=0)
        #         plt.ylabel("dose * r [MeV cm/g]")
        #         plt.ylim([(dose_mc_MeV_g * self.r_data_cm_1d).min(), (dose_mc_MeV_g * self.r_data_cm_1d).max()])
        #         plt.yscale('log')
        #         out_filename = prefix + "fit_details_{:4.3f}_r_log".format(z_cm) + suffix + '.png'
        #         logger.info('Saving ' + out_filename)
        #         plt.savefig(out_filename)
        #         plt.xscale('log')
        #         out_filename = prefix + "fit_details_{:4.3f}_r_loglog".format(z_cm) + suffix + '.png'
        #         logger.info('Saving ' + out_filename)
        #         plt.savefig(out_filename)
        #         plt.close()

    @staticmethod
    def fit_summary(fit_results):
        try:
            logging.getLogger('matplotlib').setLevel(logging.INFO)
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            # set matplotlib logging level to ERROR, in order not to pollute our log space
            logging.getLogger('matplotlib').setLevel(logging.ERROR)
        except ImportError:
            logger.error("Matplotlib not installed, output won't be generated")
            return 1
        # left Y axis dedicated to FWHM, right one to weight
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        lns1 = ax1.plot(fit_results.z_cm, fit_results.data['fwhm1_cm'], 'g', label='fwhm1')
        upper_fwhm1_line = fit_results.data['fwhm1_cm'] + fit_results.error['fwhm1_cm']
        lower_fwhm1_line = fit_results.data['fwhm1_cm'] - fit_results.error['fwhm1_cm']
        ax1.fill_between(fit_results.z_cm, lower_fwhm1_line, upper_fwhm1_line,
                         where=upper_fwhm1_line >= lower_fwhm1_line,
                         facecolor='green',
                         alpha=0.1,
                         interpolate=True)
        if fit_results.data['fwhm2_cm'].sum() > 0:
            lns2 = ax1.plot(fit_results.z_cm, fit_results.data['fwhm2_cm'], 'r', label='fwhm2')
            upper_fwhm2_line = fit_results.data['fwhm2_cm'] + fit_results.error['fwhm2_cm']
            lower_fwhm2_line = fit_results.data['fwhm2_cm'] - fit_results.error['fwhm2_cm']
            ax1.fill_between(fit_results.z_cm, lower_fwhm2_line, upper_fwhm2_line,
                             where=upper_fwhm2_line >= lower_fwhm2_line,
                             facecolor='red',
                             alpha=0.1,
                             interpolate=True)

            lns3 = ax2.plot(fit_results.z_cm, fit_results.data['factor'], 'b', label='factor')
            upper_weight_line = fit_results.data['factor'] + fit_results.error['factor']
            lower_weight_line = fit_results.data['factor'] - fit_results.error['factor']
            ax2.fill_between(fit_results.z_cm, lower_weight_line, upper_weight_line,
                             where=upper_weight_line >= lower_weight_line,
                             facecolor='blue',
                             alpha=0.1,
                             interpolate=True)
            ax2.set_ylabel('weight of FWHM1 (factor)')
            ax2.set_ylim([0, 1])
        ax1.set_xlabel('Z [cm]')
        ax1.set_ylabel('FWHM [cm]')

        # add by hand line plots and labels to legend
        line_objs = lns1
        if fit_results.data['fwhm2_cm'].sum() > 0:
            line_objs += lns2
            line_objs += lns3
        labels = [line_obj.get_label() for line_obj in line_objs]
        ax1.legend(line_objs, labels, loc=0)

        return fig
        #
        # r_step_cm = self.r_data_cm_1d[1] - self.r_data_cm_1d[0]
        # r_max_cm = self.r_data_cm_1d[-1] + 0.5 * r_step_cm

        # beam model for single gaussian is following:
        #  G(r, sigma) = 1 / (2pi sigma) * exp( - 0.5 r^2 / sigma^2)
        #  D(z,r) = D(z,0) * G(r, sigma)
        # for double gaussian it is following:
        #  D(z,r) = D(z,0) * ( w * G(r, sigma1) + (1-w) * G(r, sigma2))
        #
        # to get depth dose profile D(z) we need to calculate average dose in some volume at depth z
        # (calculating average dose in a subspace separated by two planes at z=z0 and z=z0+dz will lead to zero dose)
        # we cannot use simple arithmetic mean, as we are dealing with cylindrical scoring and bin mass depends on r
        #
        # let rmax be radius of biggest bin in cylindrical scoring
        # we calculate D(z) which will correspond to depth-dose profile measured with ion. chamber of radius rmax
        # it is basically energy E(z) deposited in slice of radius rmax and thickness dz divided by slice mass
        # D(z) = E(z) / m(z) = E(z) / (pi rmax^2 dz rho)
        # energy E(z) is the sum of energy in all cylindrical shell in a slice and can be calculated as integral
        # thin shell has surface at radius r has surface: 2 pi r dr, thus
        # E(z) = \int_0^rmax D(r,z) rho dz 2 pi r dr
        # finally:
        # D(z) = \int_0^rmax D(r,z) rho dz 2 pi r dr / (pi rmax^2 dz rho)   which leads to:
        #
        # D(z) = 2 / rmax^2 \int_0^rmax D(r,z) r dr
        #
        # for single gaussian model this gives:
        #
        # D(z) = 2 / rmax^2 \int_0^rmax D(z,0) * G(r, sigma) r dr = D(z,0) / rmax^2 \int_0^rmax G(r, sigma) r dr
        #      = D(z,0) / (2 pi sigma rmax^2) \int_0^rmax exp( - 0.5 r^2 / sigma^2) r dr
        #
        # integral \int exp( - 0.5 r^2 / sigma^2) r dr is easy to calculate:
        # https://www.wolframalpha.com/input/?i=%5Cint+exp(+-+0.5+r%5E2+%2F+sigma%5E2)+r+dr
        #
        #  \int exp( - 0.5 r^2 / sigma^2) r dr = -sigma^2 exp( - 0.5 r^2 / sigma^2)
        #
        # which leads to
        #
        # \int_0^rmax exp( - 0.5 r^2 / sigma^2) r dr = sigma^2 ( 1 - exp( - 0.5 rmax^2 / sigma^2))
        #
        # this means depth-dose curve for single gaussian model can be expressed as:
        #
        # D(z) = D(z,0) / (2 pi sigma rmax^2) * sigma^2 ( 1 - exp( - 0.5 rmax^2 / sigma^2))
        #
        # or
        #
        # D(z) = sigma * D(z,0) * ( 1 - exp( - 0.5 rmax^2 / sigma^2)) / (2 pi rmax^2)
        #
        # double gaussian can be calculated in similar way and leads to:
        #
        # D(z) = D(z,0) / (2 pi rmax^2) * ( w * sigma1 * ( 1 - exp( - 0.5 rmax^2 / sigma1^2)) +
        #                                 ( (1-w) * sigma2 * ( 1 - exp( - 0.5 rmax^2 / sigma2^2)))
        #
        #
        # if self.ngauss == 1:
        #     sigma1_cm = fwhm1_cm_data / self._sigma_to_fwhm
        #     # sigma * D(z,0) / (2 pi rmax^2)
        #     fit_dose_MeV_g = sigma1_cm * dz0_MeV_cm_g_data / (2.0 * np.pi * r_max_cm ** 2)
        #     # missing ( 1 - exp( - 0.5 rmax^2 / sigma^2))
        #     fit_dose_MeV_g *= (np.ones_like(sigma1_cm) - np.exp(-0.5 * r_max_cm / sigma1_cm**2))
        #     plt.plot(z_fitting_cm_1d, fit_dose_MeV_g, 'r', label='dose fit')
        # if self.ngauss == 2:
        #     sigma1_cm = fwhm1_cm_data / self._sigma_to_fwhm
        #     sigma2_cm = fwhm2_cm_data / self._sigma_to_fwhm
        #     w = weight_data
        #
        #     # ( w * sigma1 * ( 1 - exp( - 0.5 rmax^2 / sigma1^2))
        #     fit_dose_MeV_g = w * sigma1_cm * \
        #         (np.ones_like(sigma1_cm) - np.exp(-0.5 * r_max_cm / sigma1_cm**2))
        #
        #     # ( (1-w) * sigma2 * ( 1 - exp( - 0.5 rmax^2 / sigma2^2)))
        #     fit_dose_MeV_g += (np.ones_like(w) - w) * sigma2_cm * \
        #         (np.ones_like(sigma2_cm) - np.exp(-0.5 * r_max_cm / sigma2_cm**2))
        #
        #     # D(z,0) / (2 pi rmax^2)
        #     fit_dose_MeV_g *= dz0_MeV_cm_g_data / (2.0 * np.pi * r_max_cm ** 2)
        #     plt.plot(z_fitting_cm_1d, fit_dose_MeV_g, 'r', label='dose fit')
        #
        # plt.plot(z_fitting_cm_1d, dose_fitting_MeV_g_1d, 'b', label='dose MC')
        # plt.xlabel('z [cm]')
        # plt.ylabel('dose [MeV/g]')
        # plt.legend(loc=0)
        # out_filename = prefix + 'dose_fit.png'
        # logger.info('Saving ' + out_filename)
        # plt.savefig(out_filename)
        # if self.verbosity > 1:
        #     plt.yscale('log')
        #     out_filename = prefix + 'dose_fit_log.png'
        #     logger.info('Saving ' + out_filename)
        #     plt.savefig(out_filename)
        # plt.close()
