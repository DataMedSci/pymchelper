import logging

import numpy as np

logger = logging.getLogger(__name__)


class SHPlotDataWriter:
    def __init__(self, filename):
        self.filename = filename + ".dat"

    def write(self, detector):
        logger.info("Writing: " + self.filename)
        axis_values = [list(detector.axis_values(i, plotting_order=True)) for i in range(detector.dimension)]
        fmt = "%g" + " %g" * detector.dimension
        data = np.transpose(axis_values + [detector.data])
        np.savetxt(self.filename, data, fmt=fmt, delimiter=' ')


class SHGnuplotDataWriter:
    def __init__(self, filename):
        self.data_filename = filename + ".dat"
        self.script_filename = filename + ".plot"
        self.plot_filename = filename + ".png"

    header = """set term png
set output \"{plot_filename}\"
"""

    plotting_command = {
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
                script_file.write(self.header.format(plot_filename=self.plot_filename))
                plt_cmd = self.plotting_command[detector.dimension]
                script_file.write(plt_cmd.format(data_filename=self.data_filename))


class SHImageWriter:
    def __init__(self, filename):
        self.plot_filename = filename + ".png"
        self.colormap = SHImageWriter.default_colormap

    default_colormap = 'gnuplot2'

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
            elif detector.dimension == 2:
                ydata = detector.axis_values(1, plotting_order=True)

                xn = detector.axis_data(0, plotting_order=True).n
                yn = detector.axis_data(1, plotting_order=True).n

                xlist = np.asarray(list(xdata)).reshape(xn, yn)
                ylist = np.asarray(list(ydata)).reshape(xn, yn)
                zlist = detector.v.reshape(xn, yn)

                plt.pcolormesh(xlist, ylist, zlist, cmap=self.colormap)
                plt.colorbar()
            plt.savefig(self.plot_filename)
            plt.close()
