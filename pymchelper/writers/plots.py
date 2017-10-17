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

    def write(self, detector):
        logger.info("Writing: " + self.filename)

        data_raw = detector.data_raw
        error_raw = detector.error_raw

        # change units for LET from MeV/cm to keV/um if necessary
        # a copy of data table is made here
        from pymchelper.shieldhit.detector.detector_type import SHDetType
        if detector.dettyp in (SHDetType.dlet, SHDetType.dletg, SHDetType.tlet, SHDetType.tletg):
            data_raw = data_raw * np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um
            if not np.all(np.isnan(error_raw)) and np.any(error_raw):
                error_raw = error_raw * np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um

        # special case for 0-dim data
        if detector.dimension == 0:
            # save two numbers to the file
            if not np.all(np.isnan(error_raw)) and np.any(error_raw):
                np.savetxt(self.filename, [[detector.data_raw, detector.error_raw]], fmt="%g %g", delimiter=' ')
            else:  # save one number to the file
                np.savetxt(self.filename, [detector.data_raw], fmt="%g", delimiter=' ')
        else:
            # each axis may have different number of points, this is what we store here:
            axis_data_columns_1d = [detector.plot_axis(i).data for i in range(detector.dimension)]

            # now we calculate running index for each axis
            axis_data_columns_long = [np.meshgrid(*axis_data_columns_1d, indexing='ij')[i].ravel()
                                      for i in range(len(axis_data_columns_1d))]

            fmt = "%g" + " %g" * detector.dimension
            data_to_save = axis_data_columns_long + [data_raw]

            # if error information is present save it as additional column
            if not np.all(np.isnan(error_raw)) and np.any(error_raw):
                fmt += " %g"
                data_to_save += [error_raw]

            # transpose from rows to columns
            data_columns = np.transpose(data_to_save)

            # save space-delimited text file
            np.savetxt(self.filename, data_columns, fmt=fmt, delimiter=' ')


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

    def write(self, detector):
        # skip plotting 0-D and 3-D data
        if detector.dimension in {0, 3}:
            return

        # set labels
        plot_x_axis = detector.plot_axis(0)
        xlabel = ImageWriter._make_label(plot_x_axis.unit, plot_x_axis.name)
        if detector.dimension == 1:
            ylabel = ImageWriter._make_label(detector.unit, detector.name)
        elif detector.dimension == 2:
            plot_y_axis = detector.plot_axis(1)
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
                                                  title=detector.name))
            plt_cmd = self._plotting_command[detector.dimension]

            # add error plot if error data present
            err_cmd = ""
            if np.any(detector.error):
                err_cmd = self._error_plot_command.format(data_filename=self.data_filename)

            script_file.write(plt_cmd.format(data_filename=self.data_filename, error_plot=err_cmd))


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

    def _save_2d_error_plot(self, detector, xlist, ylist, elist, x_axis_label, y_axis_label, z_axis_label):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib import colors

        # configure logscale on X and Y axis (both for positive and negative numbers)

        fig, ax = plt.subplots(1, 1)

        if PlotAxis.x in self.axis_with_logscale:
            plt.xscale('symlog')
        if PlotAxis.y in self.axis_with_logscale:
            plt.yscale('symlog')

        if PlotAxis.z in self.axis_with_logscale:
            norm = colors.LogNorm(vmin=elist[elist > 0].min(), vmax=elist.max())
        else:
            norm = colors.Normalize(vmin=elist.min(), vmax=elist.max())

        plt.xlabel(x_axis_label)
        plt.ylabel(y_axis_label)

        mesh = plt.pcolormesh(xlist, ylist, elist.clip(0.0), cmap=self.colormap, norm=norm)
        cbar = fig.colorbar(mesh)
        cbar.set_label(label=z_axis_label, rotation=270, verticalalignment='bottom')

        base_name, _ = os.path.splitext(self.plot_filename)
        plt.savefig(base_name + "_error.png")
        plt.close()

    def write(self, detector):
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib import colors
        except ImportError:
            logger.error("Matplotlib not installed, output won't be generated")
            return

        # skip plotting 0-D and 3-D data
        if detector.dimension in (0, 3):
            return

        data_raw = detector.data_raw
        error_raw = detector.error_raw

        # change units for LET from MeV/cm to keV/um if necessary
        # a copy of datatable is made here
        from pymchelper.shieldhit.detector.detector_type import SHDetType
        if detector.dettyp in (SHDetType.dlet, SHDetType.dletg, SHDetType.tlet, SHDetType.tletg):
            data_raw = data_raw * np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um
            if not np.all(np.isnan(error_raw)) and np.any(error_raw):
                error_raw = error_raw * np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um

        logger.info("Writing: " + self.plot_filename)

        plot_x_axis = detector.plot_axis(0)

        plt.xlabel(self._make_label(plot_x_axis.unit, plot_x_axis.name))

        # configure logscale on X and Y axis (both for positive and negative numbers)
        if PlotAxis.x in self.axis_with_logscale:
            plt.xscale('symlog')

        if PlotAxis.y in self.axis_with_logscale:
            plt.yscale('symlog')

        # 1-D plotting
        if detector.dimension == 1:

            # add optional error area
            if np.any(detector.error):
                plt.fill_between(plot_x_axis.data,
                                 (data_raw - error_raw).clip(0.0),
                                 (data_raw + error_raw).clip(0.0, 1.05 * data_raw.max()),
                                 alpha=0.2, edgecolor='#CC4F1B', facecolor='#FF9848', antialiased=True)
            plt.ylabel(self._make_label(detector.unit, detector.name))
            plt.plot(plot_x_axis.data, data_raw)
        elif detector.dimension == 2:
            plot_y_axis = detector.plot_axis(1)

            xlist, ylist = np.meshgrid(plot_x_axis.data, plot_y_axis.data)

            x_axis_label = self._make_label(plot_x_axis.unit, plot_x_axis.name)
            y_axis_label = self._make_label(plot_y_axis.unit, plot_y_axis.name)
            z_axis_label = self._make_label(detector.unit, detector.name)

            # configure logscale on Z axis
            if PlotAxis.z in self.axis_with_logscale:
                norm = colors.LogNorm(vmin=data_raw[data_raw > 0].min(), vmax=data_raw.max())
            else:
                norm = colors.Normalize(vmin=data_raw.min(), vmax=data_raw.max())

            # in case differential scorer was used there is a case when axis has to be swapped
            # this happens when X-constant, Y-differential, Z-scored
            if hasattr(detector, 'dif_axis') and detector.dif_axis == 1:
                x_axis_label, y_axis_label = y_axis_label, x_axis_label
                xlist, ylist = ylist, xlist

            plt.xlabel(x_axis_label)
            plt.ylabel(y_axis_label)

            shape_tuple = (plot_y_axis.n, plot_x_axis.n)
            zlist = data_raw.reshape(shape_tuple)
            plt.pcolormesh(xlist, ylist, zlist, cmap=self.colormap, norm=norm)

            cbar = plt.colorbar()
            cbar.set_label(z_axis_label, rotation=270, verticalalignment='bottom')

        plt.savefig(self.plot_filename)
        plt.close()

        # add 2-D error plot if error data present
        if detector.dimension == 2 and not np.all(np.isnan(error_raw)) and np.any(error_raw):
            elist = error_raw.reshape(shape_tuple)
            self._save_2d_error_plot(detector, xlist, ylist, elist, x_axis_label, y_axis_label, z_axis_label)
