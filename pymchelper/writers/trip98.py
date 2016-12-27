import time
import logging
import os
import numpy as np

logger = logging.getLogger(__name__)


class TripCubeWriter:
    def __init__(self, filename, options):
        self.output_corename = filename

    def write(self, detector):
        import getpass
        from pymchelper.shieldhit.detector.detector_type import SHDetType
        from pymchelper import __version__ as _pmcversion
        # TODO add printing information how to install pytrip if it's missing
        from pytrip import __version__ as _ptversion

        pixel_size_x = (detector.xmax - detector.xmin) / detector.nx
        pixel_size_z = (detector.zmax - detector.zmin) / detector.nz

        logging.debug("psx: {:.6f} [cm]".format(pixel_size_x))
        logging.debug("psz: {:.6f} [cm]".format(pixel_size_z))

        _patient_name = "Anonymous"
        _created_by = getpass.getuser()
        _creation_info = "Created with pymchelper {:s}; using PyTRiP98 {:s}".format(_pmcversion,
                                                                                    _ptversion)

        if detector.dettyp == SHDetType.dose:

            from pytrip import dos

            cube = dos.DosCube()
            # Warning: PyTRiP cube dimensions are in [mm]
            cube.create_empty_cube(
                1.0, detector.nx, detector.ny, detector.nz,
                pixel_size=pixel_size_x * 10.0,
                slice_distance=pixel_size_z * 10.0)

            # .dos dose cubes are usually in normalized integers,
            # where "1000" equals 100.0 % dose.
            # The next are also the defaults, but just to be clear
            # this is specifially set.
            cube.data_type = "integer"
            cube.num_bytes = 2
            cube.pydata_type = np.int16

            cube.cube = detector.data.reshape(detector.nx, detector.ny, detector.nz)

            if detector.tripdose >= 0.0 and detector.tripntot > 0:
                cube.cube = (cube.cube * detector.tripntot * 1.602e-10) / detector.tripdose * 1000.0
            else:
                cube.cube = (cube.cube / cube.cube.max()) * 1200.0

            # Save proper meta information
            cube.patient_name = _patient_name
            cube.created_by = _created_by
            cube.creation_info = _creation_info

            cube.write(self.output_corename)

        elif detector.dettyp in (SHDetType.dlet, SHDetType.tlet, SHDetType.dletg, SHDetType.tletg):

            from pytrip import let

            cube = let.LETCube()
            # Warning: PyTRiP cube dimensions are in [mm]
            cube.create_empty_cube(
                1.0, detector.nx, detector.ny, detector.nz,
                pixel_size=pixel_size_x * 10.0,
                slice_distance=pixel_size_z * 10.0)

            # .dosemlet.dos LET cubes are usually in 32 bit floats.
            cube.data_type = "float"
            cube.num_bytes = 4
            cube.pydata_type = np.float32

            # need to redo the cube, since by default np.float32 are allocated.
            # When https://github.com/pytrip/pytrip/issues/35 is fixed,
            # then this should not be needed.
            cube.cube = np.ones((cube.dimz, cube.dimy, cube.dimx), dtype=cube.pydata_type)

            cube.cube = detector.data.reshape(detector.nx, detector.ny, detector.nz)
            cube.cube *= 0.1  # MeV/cm -> keV/um
            # Save proper meta information

            cube.patient_name = _patient_name
            cube.created_by = _created_by
            cube.creation_info = _creation_info

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
#   z[g/cm**2] dE/dz[MeV/(g/cm**2)] FWHM1[g/cm**2] factor FWHM2[g/cm**2]
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

            # extract data from detector data
            self._extract_data(detector)

            # in order to avoid fitting data to noisy region far behind Bragg peak tail,
            # find the range of z coordinate which containes (1-threshold) of the deposited energy
            threshold = 3e-3
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

                self._plot_2d_map(z_fitting_cm_2d, r_fitting_cm_2d, dose_fitting_MeV_g_2d, z_fitting_cm_1d)

            logger.info("Fitting...")
            fwhm1_cm_data = np.zeros_like(z_fitting_cm_1d)
            fwhm2_cm_data = np.zeros_like(z_fitting_cm_1d)
            weight_data = np.zeros_like(z_fitting_cm_1d)
            dz0_MeV_cm_g_data = np.zeros_like(z_fitting_cm_1d)
            fwhm1_cm_error_data = np.zeros_like(z_fitting_cm_1d)
            fwhm2_cm_error_data = np.zeros_like(z_fitting_cm_1d)
            weight_error_data = np.zeros_like(z_fitting_cm_1d)
            dz0_MeV_cm_g_error_data = np.zeros_like(z_fitting_cm_1d)
            if self.ngauss in (1, 2):
                # for each depth fit a lateral beam with gaussian models
                for ind, z_cm in enumerate(z_fitting_cm_1d):

                    dose_at_z = self.dose_data_MeV_g_2d[ind]

                    # take into account only this position in r for which dose is positive
                    r_fitting_cm = self.r_data_cm_1d[dose_at_z > 0]
                    dose_fitting_1d_positive_MeV_g = dose_at_z[dose_at_z > 0]

                    # perform the fit
                    params, params_error = self._lateral_fit(r_fitting_cm,
                                                             dose_fitting_1d_positive_MeV_g,
                                                             z_cm,
                                                             self.energy_MeV,
                                                             self.ngauss)

                    fwhm1_cm, factor, fwhm2_cm, dz0_MeV_cm_g = params
                    fwhm1_cm_error, factor_error, fwhm2_cm_error, dz0_MeV_cm_g_error = params_error
                    fwhm1_cm_data[ind] = fwhm1_cm
                    dz0_MeV_cm_g_data[ind] = dz0_MeV_cm_g
                    fwhm1_cm_error_data[ind] = fwhm1_cm_error
                    dz0_MeV_cm_g_error_data[ind] = dz0_MeV_cm_g_error
                    if self.ngauss == 2:
                        fwhm2_cm_data[ind] = fwhm2_cm  # set to 0 in case ngauss = 1
                        weight_data[ind] = factor  # set to 0 in case ngauss = 1
                        fwhm2_cm_error_data[ind] = fwhm2_cm_error
                        weight_error_data[ind] = factor_error

            logger.info("Plotting 2...")
            if self.verbosity > 0 and self.ngauss in (1, 2):
                self._post_fitting_plots(z_fitting_cm_1d,
                                         dose_fitting_MeV_g_1d,
                                         dz0_MeV_cm_g_data,
                                         fwhm1_cm_data,
                                         fwhm2_cm_data,
                                         weight_data,
                                         dz0_MeV_cm_g_error_data,
                                         fwhm1_cm_error_data,
                                         weight_error_data,
                                         fwhm2_cm_error_data)
                self._plot_2d_map(
                    z_fitting_cm_2d,
                    r_fitting_cm_2d,
                    dose_fitting_MeV_g_2d,
                    z_fitting_cm_1d,
                    fwhm1_cm_data,
                    fwhm2_cm_data,
                    weight_data,
                    dz0_MeV_cm_g_data,
                    suffix='_fwhm')

            logger.info("Writing " + self.ddd_filename)

            # prepare header of DDD file
            header = self._ddd_header_template.format(
                fileversion='19980520',
                filedate=time.strftime('%c'),  # Locale's appropriate date and time representation
                projectile='C',
                material='H20',
                composition='H20',
                density=1,
                energy=self.energy_MeV)

            # write the contents of the files
            with open(self.ddd_filename, 'w') as ddd_file:
                ddd_file.write(header)
                # TODO write to DDD gaussian amplitude, not the dose in central bin
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

        self.dose_error_MeV_g_2d = np.array(detector.error).reshape(detector.nz, detector.nx)

        # 1D arrays of r,z and dose in the very central bin
        self.r_data_cm_1d = self.r_data_cm_2d[0]  # middle points of the bins
        self.z_data_cm_1d = np.asarray(list(detector.z)[0:detector.nz * detector.nx:detector.nx])

        # np.savez("data", r2d=self.r_data_cm_2d, z2d=self.z_data_cm_2d, d2d=self.dose_data_MeV_g_2d,
        #          r1d=self.r_data_cm_1d, z1d=self.z_data_cm_1d, e2d=self.dose_error_MeV_g_2d)

        bin_depth_z_cm = self.z_data_cm_1d[1] - self.z_data_cm_1d[0]
        r_step_cm = self.r_data_cm_1d[1] - self.r_data_cm_1d[0]

        # i-th bin volume = dz * pi * (r_i_max^2 - r_i_min^2  )
        #   r_i_max = r_i + dr / 2
        #   r_i_min = r_i - dr / 2
        #  r_i_max^2 - r_i_min^2 = (r_i_max - r_i_min)*(r_i_max + r_i_min) = dr * 2 * r_i    thus
        # i-th bin volume = 2 * pi * dr * r_i * dz
        bin_volume_data_cm3_1d = 2.0 * np.pi * r_step_cm * self.r_data_cm_1d * bin_depth_z_cm
        # we assume density of 1 g/c3
        density_g_cm3 = 1.0
        total_bin_mass_g = density_g_cm3 * bin_depth_z_cm * np.pi * (self.r_data_cm_1d[-1] + r_step_cm/2.0)**2
        energy_in_bin_MeV_2d = self.dose_data_MeV_g_2d * bin_volume_data_cm3_1d * density_g_cm3
        total_energy_at_depth_MeV_1d = np.sum(energy_in_bin_MeV_2d, axis=1)
        self.dose_data_MeV_g_1d = total_energy_at_depth_MeV_1d / total_bin_mass_g

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
                     weight=None,
                     dz0_MeV_cm_g_data=None,
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
        if z_fitting_cm_1d is not None and np.any(fwhm1_cm):
            plt.plot(z_fitting_cm_1d, fwhm1_cm, color='g', label="fwhm1")
        if z_fitting_cm_1d is not None and np.any(fwhm2_cm):
            plt.plot(z_fitting_cm_1d, fwhm2_cm, color='r', label="fwhm2")

        # plot legend only if some of the FWHM 1-D overlays are present
        # adding legend to only pcolormesh plot will result in a warning about missing labels
        if z_fitting_cm_1d is not None and (np.any(fwhm1_cm) or np.any(fwhm2_cm)):
            plt.legend(loc=0)
        plt.xlabel("z [cm]")
        plt.ylabel("r [cm]")
        plt.xlim((z_fitting_cm_2d.min(), z_fitting_cm_2d.max()))
        if np.any(fwhm1_cm) and np.any(fwhm2_cm):
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

        if self.verbosity > 2 and (np.any(fwhm1_cm) or np.any(fwhm2_cm)):
            # TODO add plotting sum of 2 gausses
            sigma1_cm = fwhm1_cm / 2.354820045
            sigma2_cm = fwhm2_cm / 2.354820045
            gauss_amplitude_MeV_g = dz0_MeV_cm_g_data
            for z_cm, sigma1_at_z_cm, sigma2_at_z_cm, factor, amplitude_MeV_g in \
                    zip(z_fitting_cm_1d, sigma1_cm, sigma2_cm, weight, gauss_amplitude_MeV_g):
                dose_mc_MeV_g = self.dose_data_MeV_g_2d[self.z_data_cm_2d == z_cm]
                title = "Z = {:4.3f} cm,  sigma1 = {:4.3f} cm".format(z_cm, sigma1_at_z_cm)
                plt.plot(self.r_data_cm_1d, dose_mc_MeV_g, 'k.', label="data")
                if self.ngauss == 1:
                    gauss_data_MeV_g = self.gauss_MeV_g(self.r_data_cm_1d, amplitude_MeV_g, sigma1_at_z_cm)
                    plt.plot(self.r_data_cm_1d, gauss_data_MeV_g, label="fit")
                elif self.ngauss == 2:
                    gauss_data_MeV_g = self.gauss2_MeV_g(self.r_data_cm_1d, amplitude_MeV_g,
                                                         sigma1_at_z_cm, factor, sigma2_at_z_cm)
                    gauss_data_MeV_g_1st = self.gauss2_MeV_g_1st(self.r_data_cm_1d, amplitude_MeV_g,
                                                                 sigma1_at_z_cm, factor, sigma2_at_z_cm)
                    gauss_data_MeV_g_2nd = self.gauss2_MeV_g_2nd(self.r_data_cm_1d, amplitude_MeV_g,
                                                                 sigma1_at_z_cm, factor, sigma2_at_z_cm)
                    plt.plot(self.r_data_cm_1d, gauss_data_MeV_g, label="fit")
                    plt.plot(self.r_data_cm_1d, gauss_data_MeV_g_1st, label="fit 1st gauss")
                    plt.plot(self.r_data_cm_1d, gauss_data_MeV_g_2nd, label="fit 2nd gauss")
                    title += ", sigma2 = {:4.3f} cm, factor = {:4.6f}".format(sigma2_at_z_cm, factor)
                logger.debug("Plotting at " + title)
                plt.title(title)
                plt.legend(loc=0)
                plt.yscale('log')
                plt.xlabel("r [cm]")
                plt.ylabel("dose [MeV/g]")
                plt.ylim([dose_mc_MeV_g.min(), dose_mc_MeV_g.max()])
                if self.ngauss == 1:
                    plt.ylim([dose_mc_MeV_g.min(), max(gauss_data_MeV_g.max(), dose_mc_MeV_g.max())])
                out_filename = prefix + "fit_details_{:4.3f}_log".format(z_cm) + suffix + '.png'
                logger.info('Saving ' + out_filename)
                plt.savefig(out_filename)

                plt.xscale('log')
                plt.xlim([0, self.r_data_cm_1d.max()])
                out_filename = prefix + "fit_details_{:4.3f}_loglog".format(z_cm) + suffix + '.png'
                logger.info('Saving ' + out_filename)
                plt.savefig(out_filename)

                plt.xscale('linear')
                plt.xlim([0, 5.0*sigma2_at_z_cm])
                plt.ylim([dose_mc_MeV_g[self.r_data_cm_1d < 5.0*sigma2_at_z_cm].min(), dose_mc_MeV_g.max()])
                out_filename = prefix + "fit_details_{:4.3f}_small_log".format(z_cm) + suffix + '.png'
                logger.info('Saving ' + out_filename)
                plt.savefig(out_filename)

                plt.close()

                plt.plot(self.r_data_cm_1d, dose_mc_MeV_g * self.r_data_cm_1d, 'k.', label="data")
                plt.plot(self.r_data_cm_1d, gauss_data_MeV_g * self.r_data_cm_1d, label="fit")
                plt.legend(loc=0)
                plt.ylabel("dose * r [MeV cm/g]")
                plt.ylim([(dose_mc_MeV_g * self.r_data_cm_1d).min(), (dose_mc_MeV_g * self.r_data_cm_1d).max()])
                plt.yscale('log')
                out_filename = prefix + "fit_details_{:4.3f}_r_log".format(z_cm) + suffix + '.png'
                logger.info('Saving ' + out_filename)
                plt.savefig(out_filename)
                plt.xscale('log')
                out_filename = prefix + "fit_details_{:4.3f}_r_loglog".format(z_cm) + suffix + '.png'
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

        if self.verbosity > 1:
            plt.plot(z_fitting_cm_1d, dose_fitting_MeV_g_1d, 'b', label='dose')
            plt.xlabel('z [cm]')
            plt.ylabel('dose [MeV/g]')
            plt.yscale('log')
            out_filename = prefix + 'dose_log.png'
            logger.info('Saving ' + out_filename)
            plt.savefig(out_filename)
            plt.close()

    def _post_fitting_plots(self, z_fitting_cm_1d,
                            dose_fitting_MeV_g_1d,
                            dz0_MeV_cm_g_data,
                            fwhm1_cm_data,
                            fwhm2_cm_data,
                            weight_data,
                            dz0_MeV_cm_g_error_data,
                            fwhm1_cm_error_data,
                            weight_error_data,
                            fwhm2_cm_error_data):
        import matplotlib.pyplot as plt
        prefix = os.path.join(self.outputdir, 'ddd_{:3.1f}MeV_'.format(self.energy_MeV))

        # left Y axis dedicated to FWHM, right one to weight
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        lns1 = ax1.plot(z_fitting_cm_1d, fwhm1_cm_data, 'g', label='fwhm1')
        upper_fwhm1_line = fwhm1_cm_data + fwhm1_cm_error_data
        lower_fwhm1_line = fwhm1_cm_data - fwhm1_cm_error_data
        ax1.fill_between(z_fitting_cm_1d, lower_fwhm1_line, upper_fwhm1_line,
                         where=upper_fwhm1_line >= lower_fwhm1_line,
                         facecolor='green',
                         alpha=0.1,
                         interpolate=True)
        if self.ngauss == 2:
            lns2 = ax1.plot(z_fitting_cm_1d, fwhm2_cm_data, 'r', label='fwhm2')
            upper_fwhm2_line = fwhm2_cm_data + fwhm2_cm_error_data
            lower_fwhm2_line = fwhm2_cm_data - fwhm2_cm_error_data
            ax1.fill_between(z_fitting_cm_1d, lower_fwhm2_line, upper_fwhm2_line,
                             where=upper_fwhm2_line >= lower_fwhm2_line,
                             facecolor='red',
                             alpha=0.1,
                             interpolate=True)

            lns3 = ax2.plot(z_fitting_cm_1d, weight_data, 'b', label='weight')
            upper_weight_line = weight_data + weight_error_data
            lower_weight_line = weight_data - weight_error_data
            ax2.fill_between(z_fitting_cm_1d, lower_weight_line, upper_weight_line,
                             where=upper_weight_line >= lower_weight_line,
                             facecolor='blue',
                             alpha=0.1,
                             interpolate=True)
            ax2.set_ylabel('weight of FWHM1')
            ax2.set_ylim([0, 1])
        ax1.set_xlabel('z [cm]')
        ax1.set_ylabel('FWHM [cm]')

        # add by hand line plots and labels to legend
        line_objs = lns1
        if self.ngauss == 2:
            line_objs += lns2
            line_objs += lns3
        labels = [l.get_label() for l in line_objs]
        ax1.legend(line_objs, labels, loc=0)

        out_filename = prefix + 'fwhm.png'
        logger.info('Saving ' + out_filename)
        plt.savefig(out_filename)
        plt.close()

        r_step_cm = self.r_data_cm_1d[1] - self.r_data_cm_1d[0]
        r_max_cm = self.r_data_cm_1d[-1] + 0.5 * r_step_cm

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
        # energy E(z) is the sum of energy in all cylyndrical shell in a slice and can be calculated as integral
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

        if self.ngauss == 1:
            sigma1_cm = fwhm1_cm_data / 2.354820045
            # sigma * D(z,0) / (2 pi rmax^2)
            fit_dose_MeV_g = sigma1_cm * dz0_MeV_cm_g_data / (2.0 * np.pi * r_max_cm ** 2)
            # missing ( 1 - exp( - 0.5 rmax^2 / sigma^2))
            fit_dose_MeV_g *= (np.ones_like(sigma1_cm) - np.exp(-0.5 * r_max_cm / sigma1_cm**2))
            plt.plot(z_fitting_cm_1d, fit_dose_MeV_g, 'r', label='dose fit')
        if self.ngauss == 2:
            sigma1_cm = fwhm1_cm_data / 2.354820045
            sigma2_cm = fwhm2_cm_data / 2.354820045
            w = weight_data

            # ( w * sigma1 * ( 1 - exp( - 0.5 rmax^2 / sigma1^2))
            fit_dose_MeV_g = w * sigma1_cm * \
                (np.ones_like(sigma1_cm) - np.exp(-0.5 * r_max_cm / sigma1_cm**2))

            # ( (1-w) * sigma2 * ( 1 - exp( - 0.5 rmax^2 / sigma2^2)))
            fit_dose_MeV_g += (np.ones_like(w) - w) * sigma2_cm * \
                (np.ones_like(sigma2_cm) - np.exp(-0.5 * r_max_cm / sigma2_cm**2))

            # D(z,0) / (2 pi rmax^2)
            fit_dose_MeV_g *= dz0_MeV_cm_g_data / (2.0 * np.pi * r_max_cm ** 2)
            plt.plot(z_fitting_cm_1d, fit_dose_MeV_g, 'r', label='dose fit')

        plt.plot(z_fitting_cm_1d, dose_fitting_MeV_g_1d, 'b', label='dose MC')
        plt.xlabel('z [cm]')
        plt.ylabel('dose [MeV/g]')
        plt.legend(loc=0)
        out_filename = prefix + 'dose_fit.png'
        logger.info('Saving ' + out_filename)
        plt.savefig(out_filename)
        if self.verbosity > 1:
            plt.yscale('log')
            out_filename = prefix + 'dose_fit_log.png'
            logger.info('Saving ' + out_filename)
            plt.savefig(out_filename)
        plt.close()

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
            + ((1.0 - weight) / (sigma1_cm + sigma2_add_cm)) * np.exp(
                -x_cm ** 2 / (2.0 * (sigma1_cm + sigma2_add_cm) ** 2))
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

    @classmethod
    def _lateral_fit(cls, r_cm, dose_MeV_g, z_cm, energy_MeV, ngauss=2):
        variance = np.average(r_cm ** 2, weights=dose_MeV_g)

        starting_amp_MeV_g = dose_MeV_g.max()
        starting_sigma_cm = np.sqrt(variance)

        min_amp_MeV_g = 1e-10 * dose_MeV_g.max()
        min_sigma_cm = 1e-2 * starting_sigma_cm

        max_amp_MeV_g = 2.0 * dose_MeV_g.max()
        max_sigma_cm = 1e4 * starting_sigma_cm

        from scipy.optimize import curve_fit

        if ngauss == 1:
            popt, pcov = curve_fit(f=cls.gauss_r_MeV_cm_g,
                                   xdata=r_cm,
                                   ydata=dose_MeV_g * r_cm,
                                   p0=[starting_amp_MeV_g, starting_sigma_cm],
                                   bounds=([[min_amp_MeV_g, min_sigma_cm], [max_amp_MeV_g, max_sigma_cm]]),
                                   sigma=None)
            # TODO return also parameter errors
            perr = np.sqrt(np.diag(pcov))

            dz0_MeV_cm_g, sigma_cm = popt
            dz0_MeV_cm_g_error, sigma_cm_error = perr
            factor = 0.0
            factor_error = 0.0
            fwhm2_cm = 0.0
            fwhm2_cm_error = 0.0

        elif ngauss == 2:
            starting_weigth = 0.99
            starting_sigma2_add_cm = 0.1

            min_weigth = 0.55
            min_sigma2_add_cm = 1e-1

            max_weigth = 1.0 - 1e-12
            max_sigma2_add_cm = 20.0

            popt, pcov = curve_fit(f=cls.gauss2_r_MeV_cm_g,
                                   xdata=r_cm,
                                   ydata=dose_MeV_g * r_cm,
                                   p0=[starting_amp_MeV_g, starting_sigma_cm, starting_weigth, starting_sigma2_add_cm],
                                   bounds=([min_amp_MeV_g, min_sigma_cm, min_weigth, min_sigma2_add_cm],
                                           [max_amp_MeV_g, max_sigma_cm, max_weigth, max_sigma2_add_cm]),
                                   sigma=None)
            # TODO return also parameter errors
            perr = np.sqrt(np.diag(pcov))
            dz0_MeV_cm_g_error, sigma_cm_error, factor_error, sigma2_add_cm_error = perr

            dz0_MeV_cm_g, sigma_cm, factor, sigma2_add_cm = popt
            sigma2_cm = sigma_cm + sigma2_add_cm
            sigma2_cm_error = np.sqrt(sigma_cm_error**2 + sigma2_add_cm_error**2)
            fwhm2_cm = sigma2_cm * 2.354820045
            fwhm2_cm_error = sigma2_cm_error * 2.354820045

        fwhm1_cm = sigma_cm * 2.354820045

        fwhm1_cm_error = sigma_cm_error * 2.354820045

        params = fwhm1_cm, factor, fwhm2_cm, dz0_MeV_cm_g
        params_error = fwhm1_cm_error, factor_error, fwhm2_cm_error, dz0_MeV_cm_g_error

        return params, params_error
