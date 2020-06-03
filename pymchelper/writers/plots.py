import logging
import os
from enum import IntEnum

import numpy as np

logger = logging.getLogger(__name__)


class PlotAxis(IntEnum):
    x = 1
    y = 2
    z = 3


class PlotDataWriter:
    def __init__(self, filename, options):
        self.filename = filename
        if not self.filename.endswith(".dat"):
            self.filename += ".dat"

    def write(self, estimator):
        if len(estimator.pages) > 1:
            print("Conversion of data with multiple pages not supported yet")
            return False

        logger.info("Writing: " + self.filename)

        page = estimator.pages[0]

        # # change units for LET from MeV/cm to keV/um if necessary
        # # a copy of data table is made here
        # from pymchelper.shieldhit.detector.detector_type import SHDetType
        # if estimator.dettyp in (SHDetType.dlet, SHDetType.dletg, SHDetType.tlet, SHDetType.tletg):
        #     data_raw = data_raw * np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um
        #     if not np.all(np.isnan(error_raw)) and np.any(error_raw):
        #         error_raw = error_raw * np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um
        # TODO move to reader

        # special case for 0-dim data
        if page.dimension == 0:
            # save two numbers to the file
            if not np.all(np.isnan(page.error_raw)) and np.any(page.error_raw):
                np.savetxt(self.filename, [[page.data_raw, page.error_raw]], fmt="%g %g", delimiter=' ')
            else:  # save one number to the file
                np.savetxt(self.filename, [page.data_raw], fmt="%g", delimiter=' ')
        else:
            axis_numbers = list(range(page.dimension))

            # each axis may have different number of points, this is what we store here:
            axis_data_columns_1d = [page.plot_axis(i).data for i in axis_numbers]

            # now we calculate running index for each axis
            axis_data_columns_long = [np.meshgrid(*axis_data_columns_1d, indexing='ij')[i].ravel()
                                      for i in axis_numbers]

            fmt = "%g" + " %g" * page.dimension
            data_to_save = axis_data_columns_long + [page.data_raw]

            # if error information is present save it as additional column
            if not np.all(np.isnan(page.error_raw)) and np.any(page.error_raw):
                fmt += " %g"
                data_to_save += [page.error_raw]

            # transpose from rows to columns
            data_columns = np.transpose(data_to_save)

            # save space-delimited text file
            np.savetxt(self.filename, data_columns, fmt=fmt, delimiter=' ')
        return 0


class GnuplotDataWriter:
    def __init__(self, filename, options):
        self.data_filename = filename
        self.script_filename = filename
        self.plot_filename = filename

        if not self.plot_filename.endswith(".png"):
            self.plot_filename += ".png"
        if not self.script_filename.endswith(".plot"):
            self.script_filename += ".plot"
        if not self.data_filename.endswith(".dat"):
            self.data_filename += ".dat"

        dirname = os.path.split(self.script_filename)[0]
        self.awk_script_filename = os.path.join(dirname, "addblanks.awk")

    _awk_2d_script_content = """/^[[:blank:]]*#/ {next} # ignore comments (lines starting with #)
NF < 3 {next} # ignore lines which don't have at least 3 columns
$2 != prev {printf \"\\n\"; prev=$2} # print blank line
{print} # print the line
    """

    _header = """set term png
set output \"{plot_filename}\"
set title \"{title}\"
set xlabel \"{xlabel}\"
set ylabel \"{ylabel}\"
"""

    _error_plot_command = "'./{data_filename}' u 1:(max($2-$3,0.0)):($2+$3) w filledcurves " \
                          "fs transparent solid 0.2 lc 3 title '1-sigma confidence', "

    _plotting_command = {
        1: """max(x,y) = (x > y) ? x : y
plot {error_plot} './{data_filename}' u 1:2 w l lt 1 lw 2 lc -1 title 'mean value'
        """,
        2: """set view map
splot \"<awk -f addblanks.awk '{data_filename}'\" u 1:2:3 with pm3d
"""
    }

    def write(self, estimator):
        if len(estimator.pages) > 1:
            print("Conversion of data with multiple pages not supported yet")
            return False

        # skip plotting 0-D and 3-D data
        if estimator.dimension not in {1, 2}:
            return False

        page = estimator.pages[0]

        # set labels
        plot_x_axis = page.plot_axis(0)
        xlabel = ImageWriter._make_label(plot_x_axis.unit, plot_x_axis.name)
        if estimator.dimension == 1:
            ylabel = ImageWriter._make_label(page.unit, page.name)
        elif estimator.dimension == 2:
            plot_y_axis = page.plot_axis(1)
            ylabel = ImageWriter._make_label(plot_y_axis.unit, plot_y_axis.name)

            # for 2-D plots write additional awk script to convert data
            # as described in gnuplot faq: http://www.gnuplot.info/faq/faq.html#x1-320003.9
            with open(self.awk_script_filename, 'w') as script_file:
                logger.info("Writing: " + self.awk_script_filename)
                script_file.write(self._awk_2d_script_content)

        # save gnuplot script
        with open(self.script_filename, 'w') as script_file:
            logger.info("Writing: " + self.script_filename)
            script_file.write(self._header.format(plot_filename=self.plot_filename, xlabel=xlabel, ylabel=ylabel,
                                                  title=page.name))
            plt_cmd = self._plotting_command[page.dimension]

            # add error plot if error data present
            err_cmd = ""
            if np.any(page.error):
                err_cmd = self._error_plot_command.format(data_filename=self.data_filename)

            script_file.write(plt_cmd.format(data_filename=self.data_filename, error_plot=err_cmd))
        return 0


class ImageWriter:
    def __init__(self, filename, options):
        self.plot_filename = filename
        if not self.plot_filename.endswith(".png"):
            self.plot_filename += ".png"
        self.colormap = options.colormap
        self.axis_with_logscale = {PlotAxis[name] for name in options.log}

    default_colormap = 'gnuplot2'

    @staticmethod
    def _make_label(unit, name):
        return name + " " + "[" + unit + "]"

    def _save_2d_error_plot(self, xr, yr, elist, x_axis_label, y_axis_label, z_axis_label):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib import colors

        fig, ax = plt.subplots(1, 1)

        # configure logscale on X and Y axis (both for positive and negative numbers)
        if PlotAxis.x in self.axis_with_logscale:
            ax.set_xscale('symlog')
        if PlotAxis.y in self.axis_with_logscale:
            ax.set_yscale('symlog')

        if PlotAxis.z in self.axis_with_logscale:
            norm = colors.LogNorm(vmin=elist[elist > 0].min(), vmax=elist.max())
        else:
            norm = colors.Normalize(vmin=elist.min(), vmax=elist.max())

        ax.set_xlabel(x_axis_label)
        ax.set_ylabel(y_axis_label)

        mesh = ax.pcolorfast(xr, yr, elist.clip(0.0), cmap=self.colormap, norm=norm)
        cbar = fig.colorbar(mesh)
        cbar.set_label(label=z_axis_label, rotation=270, verticalalignment='bottom')

        base_name, _ = os.path.splitext(self.plot_filename)
        fig.savefig(base_name + "_error.png")
        plt.close(fig)

    def write(self, estimator):

        if len(estimator.pages) > 1:
            print("Conversion of data with multiple pages not supported yet")
            return False

        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib import colors
        except ImportError:
            logger.error("Matplotlib not installed, output won't be generated")
            return 1

        page = estimator.pages[0]

        # skip plotting 1-D and 3-D and higher dimensional data
        if page.dimension not in (1, 2):
            return 0

        data_raw = page.data_raw
        error_raw = page.error_raw

        # change units for LET from MeV/cm to keV/um if necessary
        # a copy of datatable is made here
        # from pymchelper.shieldhit.detector.detector_type import SHDetType
        # if estimator.dettyp in (SHDetType.dlet, SHDetType.dletg, SHDetType.tlet, SHDetType.tletg):
        #     data_raw = data_raw * np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um
        #     if not np.all(np.isnan(error_raw)) and np.any(error_raw):
        #         error_raw = error_raw * np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um
        # TODO - move units change to reader !

        logger.info("Writing: " + self.plot_filename)

        plot_x_axis = page.plot_axis(0)

        fig, ax = plt.subplots()
        ax.set_xlabel(self._make_label(plot_x_axis.unit, plot_x_axis.name))

        # configure logscale on X and Y axis (both for positive and negative numbers)
        if PlotAxis.x in self.axis_with_logscale:
            ax.set_xscale('symlog')

        if PlotAxis.y in self.axis_with_logscale:
            ax.set_yscale('symlog')

        # 1-D plotting
        if page.dimension == 1:

            # add optional error area
            if np.any(page.error):
                ax.fill_between(plot_x_axis.data,
                                (data_raw - error_raw).clip(0.0),
                                (data_raw + error_raw).clip(0.0, 1.05 * data_raw.max()),
                                alpha=0.2, edgecolor='#CC4F1B', facecolor='#FF9848', antialiased=True)
            ax.set_ylabel(self._make_label(page.unit, page.name))
            ax.plot(plot_x_axis.data, data_raw)
        elif page.dimension == 2:
            plot_y_axis = page.plot_axis(1)

            x_axis_label = self._make_label(plot_x_axis.unit, plot_x_axis.name)
            y_axis_label = self._make_label(plot_y_axis.unit, plot_y_axis.name)
            z_axis_label = self._make_label(page.unit, page.name)

            # configure logscale on Z axis
            if PlotAxis.z in self.axis_with_logscale:
                norm = colors.LogNorm(vmin=data_raw[data_raw > 0].min(), vmax=data_raw.max())
            else:
                norm = colors.Normalize(vmin=data_raw.min(), vmax=data_raw.max())

            xspan = [plot_x_axis.min_val, plot_x_axis.max_val]
            yspan = [plot_y_axis.min_val, plot_y_axis.max_val]
            zdata = data_raw.reshape((plot_y_axis.n, plot_x_axis.n))

            plt.xlabel(x_axis_label)
            plt.ylabel(y_axis_label)

            im = ax.pcolorfast(xspan, yspan, zdata, cmap=self.colormap, norm=norm)

            cbar = plt.colorbar(im)
            if PlotAxis.z in self.axis_with_logscale:
                import matplotlib.ticker as ticker
                cbar.set_ticks(ticker.LogLocator(subs='all', numticks=15))
            cbar.set_label(z_axis_label, rotation=270, verticalalignment='bottom')

        fig.savefig(self.plot_filename)
        plt.close(fig)

        # add 2-D error plot if error data present
        if estimator.dimension == 2 and not np.all(np.isnan(error_raw)) and np.any(error_raw):
            edata = error_raw.reshape((plot_y_axis.n, plot_x_axis.n))
            self._save_2d_error_plot(xspan, yspan, edata, x_axis_label, y_axis_label, z_axis_label)

        return 0
