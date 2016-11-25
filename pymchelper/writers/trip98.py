import time
import logging
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

                self._plot_2d_map(z_fitting_cm_2d, r_fitting_cm_2d, dose_fitting_MeV_g_2d, z_fitting_cm_1d, None, None)

            logger.info("Fitting...")
            fwhm1_cm_data = []
            fwhm2_cm_data = []
            weight_data = []
            dz0_MeV_cm_g_data = []
            if self.ngauss in (1, 2):
                # for each depth fit a lateral beam with gaussian models
                for z_cm, dose_at_z in zip(z_fitting_cm_1d, self.dose_data_MeV_g_2d[:thr_ind]):

                    # take into account only this position in r for which dose is positive
                    r_fitting_cm = self.r_data_cm_1d[dose_at_z > 0]
                    dose_fitting_1d_positive_MeV_g = dose_at_z[dose_at_z > 0]

                    # fitting will be done on D(r)*r data
                    radial_dose_MeV_cm_g = dose_fitting_1d_positive_MeV_g * r_fitting_cm

                    # perform the fit
                    fwhm1_cm, factor, fwhm2_cm, dz0_MeV_cm_g = self._lateral_fit(r_fitting_cm,
                                                                                 radial_dose_MeV_cm_g,
                                                                                 z_cm,
                                                                                 self.energy_MeV,
                                                                                 self.ngauss)

                    fwhm1_cm_data.append(fwhm1_cm)
                    dz0_MeV_cm_g_data.append(dz0_MeV_cm_g)
                    if self.ngauss == 2:
                        fwhm2_cm_data.append(fwhm2_cm)  # set to 0 in case ngauss = 1
                        weight_data.append(factor)  # set to 0 in case ngauss = 1

            logger.info("Plotting 2...")
            if self.verbosity > 0 and self.ngauss in (1, 2):
                self._post_fitting_plots(z_fitting_cm_1d,
                                         dose_fitting_MeV_g_1d,
                                         dz0_MeV_cm_g_data,
                                         fwhm1_cm_data,
                                         fwhm2_cm_data,
                                         weight_data)
                self._plot_2d_map(
                    z_fitting_cm_2d,
                    r_fitting_cm_2d,
                    dose_fitting_MeV_g_2d,
                    z_fitting_cm_1d,
                    fwhm1_cm_data,
                    fwhm2_cm_data,
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

        # 1D arrays of r,z and dose in the very central bin
        self.r_data_cm_1d = self.r_data_cm_2d[0]  # middle points of the bins
        self.z_data_cm_1d = np.asarray(list(detector.z)[0:detector.nz * detector.nx:detector.nx])
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
        if z_fitting_cm_1d is not None and fwhm1_cm:
            plt.plot(z_fitting_cm_1d, fwhm1_cm, color='g', label="fwhm1")
        if z_fitting_cm_1d is not None and fwhm2_cm:
            plt.plot(z_fitting_cm_1d, fwhm2_cm, color='r', label="fwhm2")

        # plot legend only if some of the FWHM 1-D overlays are present
        # adding legend to only pcolormesh plot will result in a warning about missing labels
        if z_fitting_cm_1d is not None and (fwhm1_cm or fwhm2_cm):
            plt.legend(loc=0)
        plt.xlabel("z [cm]")
        plt.ylabel("r [cm]")
        plt.xlim((z_fitting_cm_2d.min(), z_fitting_cm_2d.max()))
        if fwhm1_cm and fwhm2_cm:
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

        if self.verbosity > 2 and (fwhm1_cm or fwhm2_cm):
            sigma1_cm = np.array(fwhm1_cm) / 2.354820045
            gauss_amplitude_MeV_g = dz0_MeV_cm_g_data / (2.0 * np.pi * sigma1_cm**2)
            for z_cm in self.z_data_cm_1d:
                z_filter_1d = (z_fitting_cm_1d == z_cm)
                sigma1_at_z_cm = sigma1_cm[z_filter_1d]
                dose_mc_MeV_g = self.dose_data_MeV_g_2d[self.z_data_cm_2d == z_cm]
                title = "Z = {:4.3f} cm,  sigma1 = {:4.3f} cm".format(z_cm, sigma1_at_z_cm[0])
                logger.debug("Plotting at " + title)
                plt.title(title)
                plt.plot(self.r_data_cm_1d, dose_mc_MeV_g)
                if self.ngauss == 1:
                    gauss_data_MeV_g = gauss_amplitude_MeV_g[z_filter_1d] * \
                                       np.exp(-0.5 * self.r_data_cm_1d**2 / sigma1_at_z_cm)
                    plt.plot(self.r_data_cm_1d, gauss_data_MeV_g)
                plt.yscale('log')
                plt.xlabel("r [cm]")
                plt.ylabel("dose [MeV/g]")
                # plt.xlim([0, 5*sigma1_at_z_cm])
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
                plt.close()

                plt.plot(self.r_data_cm_1d, dose_mc_MeV_g * self.r_data_cm_1d)
                if self.ngauss == 1:
                    plt.plot(self.r_data_cm_1d, gauss_data_MeV_g * self.r_data_cm_1d)
                plt.ylabel("dose * r [MeV cm/g]")
                # plt.xlim([0, 5*sigma1_at_z_cm])
                plt.ylim([(dose_mc_MeV_g * self.r_data_cm_1d).min(), (dose_mc_MeV_g * self.r_data_cm_1d).max()])
                if self.ngauss == 1:
                    plt.ylim([(dose_mc_MeV_g * self.r_data_cm_1d).min(),
                              max(gauss_data_MeV_g.max(), (dose_mc_MeV_g * self.r_data_cm_1d).max())])
                out_filename = prefix + "fit_details_{:4.3f}_r".format(z_cm) + suffix + '.png'
                logger.info('Saving ' + out_filename)
                plt.savefig(out_filename)
                plt.yscale('log')
                out_filename = prefix + "fit_details_{:4.3f}_r_log".format(z_cm) + suffix + '.png'
                logger.info('Saving ' + out_filename)
                plt.savefig(out_filename)
                plt.xscale('log')
                plt.xlim([0, self.r_data_cm_1d.max()])
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

    def _post_fitting_plots(self, z_fitting_cm_1d,
                            dose_fitting_MeV_g_1d,
                            dz0_MeV_cm_g_data,
                            fwhm1_cm_data,
                            fwhm2_cm_data,
                            weight_data):
        import matplotlib.pyplot as plt
        prefix = os.path.join(self.outputdir, 'ddd_{:3.1f}MeV_'.format(self.energy_MeV))

        # left Y axis dedicated to FWHM, right one to weight
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        lns1 = ax1.plot(z_fitting_cm_1d, fwhm1_cm_data, 'g', label='fwhm1')
        if fwhm2_cm_data:
            lns2 = ax1.plot(z_fitting_cm_1d, fwhm2_cm_data, 'r', label='fwhm2')
        if weight_data:
            lns3 = ax2.plot(z_fitting_cm_1d, weight_data, 'b', label='weight')
            ax2.set_ylabel('weight of FWHM1')
            ax2.set_ylim([0, 1])
        ax1.set_xlabel('z [cm]')
        ax1.set_ylabel('FWHM [cm]')

        # add by hand line plots and labels to legend
        line_objs = lns1
        if fwhm2_cm_data:
            line_objs += lns2
        if weight_data:
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
            sigma1_cm = np.array(fwhm1_cm_data) / 2.354820045
            # sigma * D(z,0) / (2 pi rmax^2)
            fit_dose_MeV_g = sigma1_cm * dz0_MeV_cm_g_data / (2.0 * np.pi * r_max_cm ** 2)
            # missing ( 1 - exp( - 0.5 rmax^2 / sigma^2))
            fit_dose_MeV_g /= (np.ones_like(sigma1_cm) - np.exp(-0.5 * r_max_cm / sigma1_cm**2))
            plt.plot(z_fitting_cm_1d, fit_dose_MeV_g, 'r', label='dose fit')
        if self.ngauss == 2:
            sigma1_cm = np.array(fwhm1_cm_data) / 2.354820045
            sigma2_cm = np.array(fwhm2_cm_data) / 2.354820045
            w = np.asarray(weight_data)

            # ( w * sigma1 * ( 1 - exp( - 0.5 rmax^2 / sigma1^2))
            fit_dose_MeV_g = w * sigma1_cm * \
                (np.ones_like(sigma1_cm) - np.exp(-0.5 * r_max_cm / sigma1_cm**2))

            # ( (1-w) * sigma2 * ( 1 - exp( - 0.5 rmax^2 / sigma2^2)))
            fit_dose_MeV_g += (np.ones_like(w) - w) * sigma2_cm * \
                (np.ones_like(sigma2_cm) - np.exp(-0.5 * r_max_cm / sigma2_cm**2))

            # D(z,0) / (2 pi rmax^2)
            fit_dose_MeV_g *= dz0_MeV_cm_g_data / (2.0 * np.pi * r_max_cm ** 2)
            plt.plot(z_fitting_cm_1d, fit_dose_MeV_g, 'r', label='dose fit')

        plt.plot(z_fitting_cm_1d, dose_fitting_MeV_g_1d, 'g', label='dose MC')
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
        a1_guess = y.max()  # guess for the amplitude of the first gaussian
        mu = 0  # set the mean to zero - a guess would be: sum(x*y)/sum(y)
        if sum(y) == 0:  # check if denominator is 0
            sigma1_cm_guess = 1e5
        else:
            sigma1_cm_guess = np.sqrt(abs(sum((x - mu)**2 * y) / sum(y)))  # guess for the deviation

        if ngauss == 2:
            a2_guess = deepcopy(a1_guess) * 0.05  # guess for the  amplitude of the second gaussian
            sigma2_cm_guess = 2  # guess for the deviation of the second gaussian
            sigma2_cm_guess = deepcopy(sigma1_cm_guess) * 5.0
            # Collect the guesses in an array
            p0 = np.asarray([a1_guess, sigma1_cm_guess, a2_guess, sigma2_cm_guess])
            bounds = [(0, 1e6), (0, 1e6), (0, 1e6), (0, 1e6)]  # set bound for the parameters,
            # they should be non-negative
            plsq = leastsqbound(residuals_2g, p0, bounds, args=(y, x), maxfev=5000)  # Calculate the fit
        elif ngauss == 1:
            # Collect the guesses in an array
            p0 = np.asarray([a1_guess, sigma1_cm_guess])
            bounds = [(0, 1e6), (0, 1e6)]  # set bound for the parameters, they should be non-negative
            plsq = leastsqbound(residuals_1g, p0, bounds, args=(y, x), maxfev=5000)  # Calculate the fit

        pfinal = plsq[0]  # final parameters
        # covar = plsq[1]  # covariance matrix

        sigma1_cm = pfinal[1]
        a1_MeV_g = pfinal[0]

        # Calculate the output parameters
        # FWHM = sqrt(8*log(2)) * Gaussian_Sigma
        fwhm1_cm = 2.354820045 * sigma1_cm  # Full Width at Half Maximum for the first Gaussian
        if ngauss == 2:
            sigma2_cm = pfinal[3]
            a2_MeV_g = pfinal[2]
            fwhm2_cm = 2.354820045 * sigma2_cm  # Full Width at Half Maximum for the second Gaussian

            # double gaussian model is following
            #  G(r, sigma) = 1 / (2pi sigma) * exp( - 0.5 r^2 / sigma^2)
            #  D(z,r) = D(z,0) * G(r, sigma)
            # for double gaussian it is following:
            #  D(z,r) = D(z,0) * ( w * G(r, sigma1) + (1-w) * G(r, sigma2))
            #
            # which can be written as:
            #
            # D(z,r) = D(z,0) * w / (2 pi sigma1) * exp( - 0.5 r^2 / sigma1^2) +
            #          D(z,0) * (1-w) / (2 pi sigma1) * exp( - 0.5 r^2 / sigma2^2)
            #
            # if we compare this with fitting model:
            #
            # D(z,r) = a1 * exp( - 0.5 r^2 / sigma1^2) + a2 * exp( - 0.5 r^2 / sigma2^2)
            #
            # then we have following equations:
            #
            # a1 = D(z,0) * w / (2 pi sigma1)
            # a2 = D(z,0) * (1-w) / (2 pi sigma2)
            #
            # which leads to:
            #
            # D(z,0) * w = 2 pi a1 sigma1
            # D(z,0) * (1-w) = 2 pi a2 sigma2
            #
            # and:
            #
            # D(z,0) = 2 pi (a1 sigma1 + a2 sigma2)
            #      w = a1 sigma1 / (a1 sigma1 + a2 sigma2)

            dz0_MeV_cm_g = 2.0 * np.pi * (a1_MeV_g * sigma1_cm + a2_MeV_g * sigma2_cm)
            factor = a1_MeV_g * sigma1_cm / (a1_MeV_g * sigma1_cm + a2_MeV_g * sigma2_cm)
        else:

            # single gaussian model is following
            #  G(r, sigma) = 1 / (2pi sigma) * exp( - 0.5 r^2 / sigma^2)
            #  D(z,r) = D(z,0) * G(r, sigma)
            #
            # which can be written as:
            #
            # D(z,r) = D(z,0) / (2 pi sigma1) * exp( - 0.5 r^2 / sigma1^2)
            #
            # if we compare this with fitting model:
            #
            # D(z,r) = a1 * exp( - 0.5 r^2 / sigma1^2)
            #
            # then we have following equation:
            #
            # a1 = D(z,0) / (2 pi sigma1)
            #
            # which leads to:
            #
            # D(z,0) = 2 pi a1 sigma1

            dz0_MeV_cm_g = 2.0 * np.pi * a1_MeV_g * sigma1_cm
            factor = 0.0
            fwhm2_cm = 0.0

        # TODO what are really the units ? DDD files in TRiP98 distribution have [cm], not [mm]
        # Scale from cm to mm according to Gheorghe from Marburg
        # fwhm1 *= 10.0
        # fwhm2 *= 10.0

        return fwhm1_cm, factor, fwhm2_cm, dz0_MeV_cm_g
