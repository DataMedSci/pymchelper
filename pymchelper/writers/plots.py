import os
import logging

import numpy as np

logger = logging.getLogger(__name__)


class PlotDataWriter:
    def __init__(self, filename, options):
        self.filename = filename
        if not self.filename.endswith(".dat"):
            self.filename += ".dat"

    def write(self, detector):
        logger.info("Writing: " + self.filename)

        data = np.array(detector.data)
        error = np.array(detector.error)

        # change units for LET from MeV/cm to keV/um
        from pymchelper.shieldhit.detector.detector_type import SHDetType
        if detector.dettyp in (SHDetType.dlet, SHDetType.dletg, SHDetType.tlet, SHDetType.tletg):
            data *= np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um
            if np.any(error):
                error *= np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um

        axis_data_column = [list(detector.axis_values(i, plotting_order=True)) for i in range(detector.dimension)]

        fmt = "%g" + " %g" * detector.dimension
        data_to_save = axis_data_column + [data.ravel()]  # ravel needed to change arrays like [[1]] to [1]

        # if error information is present save it as additional column
        if detector.error is not None:
            fmt += " %g"
            data_to_save += [error.ravel()]

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
        if detector.dimension in (0, 3):
            return

        # set labels
        x_axis_number = detector.axis_data(0, plotting_order=True).number
        xlabel = detector.units[x_axis_number]
        if detector.dimension == 1:
            ylabel = ImageWriter.make_label(detector.units[4], detector.title)
        elif detector.dimension == 2:
            y_axis_number = detector.axis_data(1, plotting_order=True).number
            ylabel = detector.units[y_axis_number]

            # for 2-D plots writte additional awk script to convert data
            # as described in gnuplot faq: http://www.gnuplot.info/faq/faq.html#x1-320003.9
            with open(self.awk_script_filename, 'w') as script_file:
                logger.info("Writing: " + self.awk_script_filename)
                script_file.write(self._awk_2d_script_content)

        # save gnuplot script
        with open(self.script_filename, 'w') as script_file:
            logger.info("Writing: " + self.script_filename)
            script_file.write(self._header.format(plot_filename=self.plot_filename, xlabel=xlabel, ylabel=ylabel,
                                                  title=detector.title))
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

    default_colormap = 'gnuplot2'

    @staticmethod
    def make_label(unit, name):
        return name + " " + "[" + unit + "]"

    def _save_2d_error_plot(self, detector, xlist, ylist, elist):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        plt.pcolormesh(xlist, ylist, elist.clip(0.0), cmap=self.colormap)
        plt.ylabel(detector.units[1])
        cbar = plt.colorbar()
        cbar.set_label(detector.units[4], rotation=270, verticalalignment='bottom')
        base_name, _ = os.path.splitext(self.plot_filename)
        plt.savefig(base_name + "_error.png")
        plt.close()

    def write(self, detector):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        # skip plotting 0-D and 3-D data
        if detector.dimension in (0, 3):
            return

        data = np.array(detector.data)
        error = np.array(detector.error)

        # change units for LET from MeV/cm to keV/um
        from pymchelper.shieldhit.detector.detector_type import SHDetType
        if detector.dettyp in (SHDetType.dlet, SHDetType.dletg, SHDetType.tlet, SHDetType.tletg):
            data *= np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um
            if np.any(error):
                error *= np.float64(0.1)  # 1 MeV / cm = 0.1 keV / um

        logger.info("Writing: " + self.plot_filename)

        x_axis_number = detector.axis_data(0, plotting_order=True).number
        plt.xlabel(self.make_label(detector.units[x_axis_number], ""))
        xlist = list(detector.axis_values(0, plotting_order=True))  # make list of values from generator

        # 1-D plotting
        if detector.dimension == 1:

            # add optional error area
            if np.any(detector.error):
                plt.fill_between(xlist,
                                 (data - error).clip(0.0),
                                 (data + error).clip(0.0, 1.05 * (detector.v.max())),
                                 alpha=0.2, edgecolor='#CC4F1B', facecolor='#FF9848', antialiased=True)
            plt.ylabel(self.make_label(detector.units[4], detector.title))
            plt.plot(xlist, data)
        elif detector.dimension == 2:
            ylist = list(detector.axis_values(1, plotting_order=True))   # make list of values from generator

            xn = detector.axis_data(0, plotting_order=True).n
            yn = detector.axis_data(1, plotting_order=True).n

            shape_tuple = (yn, xn)
            xlist = np.asarray(xlist).reshape(shape_tuple)
            ylist = np.asarray(ylist).reshape(shape_tuple)
            zlist = data.reshape(shape_tuple)

            # add error plot if error data present
            if np.any(detector.error):
                elist = error.reshape(shape_tuple)
                self._save_2d_error_plot(detector, xlist, ylist, elist)

            y_axis_number = detector.axis_data(1, plotting_order=True).number
            plt.ylabel(detector.units[y_axis_number])
            plt.pcolormesh(xlist, ylist, zlist, cmap=self.colormap)
            cbar = plt.colorbar()
            cbar.set_label(detector.units[4], rotation=270, verticalalignment='bottom')
        plt.savefig(self.plot_filename)
        plt.close()
