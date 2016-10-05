import logging

import numpy as np

logger = logging.getLogger(__name__)


class SHPlotDataWriter:
    def __init__(self, filename):
        self.filename = filename
        if not self.filename.endswith(".dat"):
            self.filename += ".dat"

    def write(self, detector):
        logger.info("Writing: " + self.filename)
        axis_values = [list(detector.axis_values(i, plotting_order=True)) for i in range(detector.dimension)]
        fmt = "%g" + " %g" * detector.dimension
        data = np.transpose(axis_values + [detector.data])
        np.savetxt(self.filename, data, fmt=fmt, delimiter=' ')


class SHGnuplotDataWriter:
    def __init__(self, filename):
        self.data_filename = filename
        self.script_filename = filename
        self.plot_filename = filename

        if not self.plot_filename.endswith(".png"):
            self.plot_filename += ".png"
        if not self.script_filename.endswith(".plot"):
            self.script_filename += ".plot"
        if not self.data_filename.endswith(".dat"):
            self.data_filename += ".dat"

    _header = """set term png
set output \"{plot_filename}\"
"""

    _plotting_command = {
        1: """plot './{data_filename}' w l
        """,
        2: """set pm3d interpolate 0,0
set view map
set dgrid3d
splot '{data_filename}' with pm3d
"""
    }

    def write(self, detector):
        if detector.dimension in (1, 2):
            with open(self.script_filename, 'w') as script_file:
                logger.info("Writing: " + self.script_filename)
                script_file.write(self._header.format(plot_filename=self.plot_filename))
                plt_cmd = self._plotting_command[detector.dimension]
                script_file.write(plt_cmd.format(data_filename=self.data_filename))


class SHImageWriter:
    def __init__(self, filename):
        self.plot_filename = filename
        if not self.plot_filename.endswith(".png"):
            self.plot_filename += ".png"
        self.colormap = SHImageWriter.default_colormap

    default_colormap = 'gnuplot2'

    @staticmethod
    def make_label(unit, name):
        return name + " " + "[" + unit + "]"

    def set_colormap(self, colormap):
        self.colormap = colormap

    def write(self, detector):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        xdata = detector.axis_values(0, plotting_order=True)

        if detector.dimension in (1, 2):
            logger.info("Writing: " + self.plot_filename)
            if detector.dimension == 1:
                plt.plot(list(xdata), detector.v)
                plt.xlabel(self.make_label(detector.units[0], ""))
                plt.ylabel(self.make_label(detector.units[4], detector.title))
            elif detector.dimension == 2:
                ydata = detector.axis_values(1, plotting_order=True)

                xn = detector.axis_data(0, plotting_order=True).n
                yn = detector.axis_data(1, plotting_order=True).n

                xlist = np.asarray(list(xdata)).reshape(xn, yn)
                ylist = np.asarray(list(ydata)).reshape(xn, yn)
                zlist = detector.v.reshape(xn, yn)

                plt.pcolormesh(xlist, ylist, zlist, cmap=self.colormap)
                cbar = plt.colorbar()
                cbar.set_label(detector.units[4], rotation=270)
                plt.xlabel(detector.units[0])
                plt.ylabel(detector.units[1])
            plt.savefig(self.plot_filename)
            plt.close()
