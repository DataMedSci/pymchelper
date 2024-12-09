import logging
import os
from enum import IntEnum
from pathlib import Path

import numpy as np
from pymchelper.page import Page

from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.writers.writer import Writer

logger = logging.getLogger(__name__)


class PlotAxis(IntEnum):
    x = 1
    y = 2
    z = 3


class PlotDataWriter(Writer):
    """plot data writer"""

    def __init__(self, output_path: str, _):
        super().__init__(output_path)
        self.output_path = self.output_path.with_suffix(".dat")

    def write_single_page(self, page: Page, output_path: Path):
        """TODO"""
        logger.info("Writing page to: %s", str(output_path))

        # special case for MCPL data
        if page.dettyp == SHDetType.mcpl:
            np.savetxt(output_path, page.data.T, fmt="%g", delimiter=' ')
            return

        # special case for 0-dim data
        if page.dimension == 0:
            # save two numbers to the file
            if page.error is not None:
                np.savetxt(self.output_path, [[page.data_raw, page.error_raw]], fmt="%g %g", delimiter=' ')
            else:  # save one number to the file
                np.savetxt(self.output_path, [page.data_raw], fmt="%g", delimiter=' ')
        else:
            axis_numbers = list(range(page.dimension))

            # each axis may have different number of points, this is what we store here:
            axis_data_columns_1d = [page.plot_axis(i).data for i in axis_numbers]

            # now we calculate running index for each axis
            axis_data_columns_long = [
                np.meshgrid(*axis_data_columns_1d, indexing='ij')[i].ravel() for i in axis_numbers
            ]

            fmt = "%g" + " %g" * page.dimension
            data_to_save = axis_data_columns_long + [page.data_raw]

            # if error information is present save it as additional column
            if page.error is not None:
                fmt += " %g"
                data_to_save += [page.error_raw]

            # transpose from rows to columns
            data_columns = np.transpose(data_to_save)

            # save space-delimited text file
            np.savetxt(output_path, data_columns, fmt=fmt, delimiter=' ')
        return


class ImageWriter:
    """Writer responsible for creating PNG images using matplotlib library"""

    def __init__(self, filename, options):
        logger.info("{:s} options:  {:s}".format(repr(self.__class__), repr(options)))
        self.plot_filename = filename
        if not self.plot_filename.endswith(".png"):
            self.plot_filename += ".png"
        self.colormap = options.colormap
        self.axis_with_logscale = {PlotAxis[name] for name in options.log}

    default_colormap = 'gnuplot2'

    @staticmethod
    def _make_label(unit, name):
        """Make label for plot axis"""
        return name + " " + "[" + unit + "]"

    def get_page_figure(self, page):
        """Calculate matplotlib figure object for a single page in estimator"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib import colors
            # set matplotlib logging level to ERROR, in order not to pollute our log space
            logging.getLogger('matplotlib').setLevel(logging.ERROR)
        except ImportError:
            logger.error("Matplotlib not installed, output won't be generated")
            return None

        # skip plotting 1-D and 3-D and higher dimensional data
        if page.dimension not in (1, 2):
            return None

        data_raw = page.data_raw
        error_raw = page.error_raw

        plot_x_axis = page.plot_axis(0)

        fig, ax = plt.subplots()
        ax.set_xlabel(self._make_label(plot_x_axis.unit, plot_x_axis.name))

        # we use symmetrical logarithmic scale as horizontal (X) axis for 1D and 2D plots
        # can have negative values as well (i.e. span from -4. to 4.)
        if PlotAxis.x in self.axis_with_logscale:
            ax.set_xscale('symlog')

        # 1-D plotting
        if page.dimension == 1:

            # scored values cannot be negative, hence we use purely logarithmic scale for vertical axis
            if PlotAxis.y in self.axis_with_logscale:
                ax.set_yscale('log')

            # add optional error area
            if page.error is not None:
                ax.fill_between(plot_x_axis.data, (data_raw - error_raw).clip(0.0),
                                (data_raw + error_raw).clip(0.0, 1.05 * data_raw.max()),
                                alpha=0.2,
                                edgecolor='#CC4F1B',
                                facecolor='#FF9848',
                                antialiased=True)
            ax.set_ylabel(self._make_label(page.unit, page.name))
            ax.grid(True, alpha=0.3)
            ax.plot(plot_x_axis.data, data_raw)
        elif page.dimension == 2:
            plot_y_axis = page.plot_axis(1)

            x_axis_label = self._make_label(plot_x_axis.unit, plot_x_axis.name)
            y_axis_label = self._make_label(plot_y_axis.unit, plot_y_axis.name)
            z_axis_label = self._make_label(page.unit, page.name)

            # we use symmetrical logarithmic scale as vertical (Y) axis for 2D plots
            # can have negative values as well (i.e. span from -4. to 4.)
            if PlotAxis.y in self.axis_with_logscale:
                ax.set_yscale('symlog')

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

            plt.grid(True, alpha=0.3)

            im = ax.pcolorfast(xspan, yspan, zdata, cmap=self.colormap, norm=norm)
            cbar = plt.colorbar(im)
            if PlotAxis.z in self.axis_with_logscale:
                import matplotlib.ticker as ticker
                cbar.set_ticks(ticker.LogLocator(subs='all', numticks=15))
            cbar.set_label(z_axis_label, rotation=270, verticalalignment='bottom')

        return fig

    def write(self, estimator):
        """Go through all pages in estimator and save corresponding figure to an output file"""
        # save single page to a file without number (i.e. output.png)
        if len(estimator.pages) == 1:
            fig = self.get_page_figure(estimator.pages[0])
            if fig:
                logger.info("Writing {}".format(self.plot_filename))
                fig.savefig(self.plot_filename)
        else:
            # split output path into directory, basename and extension
            dir_path = os.path.dirname(self.plot_filename)
            if not os.path.exists(dir_path):
                logger.info("Creating {}".format(dir_path))
                os.makedirs(dir_path)
            file_base_part, file_ext = os.path.splitext(os.path.basename(self.plot_filename))

            # loop over all pages and save an image for each of them
            for i, page in enumerate(estimator.pages):

                # calculate output filename. it will include page number padded with zeros.
                # for 10-99 pages the filename would look like: output_p01.png, ... output_p99.png
                # for 100-999 pages the filename would look like: output_p001.png, ... output_p999.png
                zero_padded_page_no = str(i + 1).zfill(len(str(len(estimator.pages))))
                output_filename = f"{file_base_part:s}_p{zero_padded_page_no:s}{file_ext:s}"
                output_path = os.path.join(dir_path, output_filename)

                # save the output file
                fig = self.get_page_figure(page)
                if fig:
                    logger.info("Writing %s", output_path)
                    try:
                        fig.savefig(output_path)
                    except ValueError as e:
                        logger.error("Failed to save plot to file: %s", output_path)
                        logger.error("Error: %s", e)
                        logger.error("Trying to save plot using different font")
                        # on some HPC system I get the error
                        # "findfont: Generic family 'sans-serif' not found ..."
                        # therefore I choose a different font
                        import matplotlib
                        matplotlib.use('Agg')
                        import matplotlib.pyplot as plt
                        plt.rcParams['font.sans-serif'] = ["DejaVu Sans Mono"]
                        plt.rcParams['font.family'] = "sans-serif"
                        fig.savefig(output_path)

        return 0
