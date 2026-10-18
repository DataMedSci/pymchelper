import logging
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
            if page.error_raw is not None:
                np.savetxt(output_path, [[page.data_raw, page.error_raw]], fmt="%g %g", delimiter=' ')
            else:  # save one number to the file
                np.savetxt(output_path, [page.data_raw], fmt="%g", delimiter=' ')
        else:
            # Create coordinate meshgrids for all dimensions
            axis_numbers = list(range(page.dimension))
            axis_data_arrays = [page.plot_axis(i).data for i in axis_numbers]

            # Generate meshgrids for each axis to create coordinate columns
            coordinate_meshgrids = np.meshgrid(*axis_data_arrays, indexing='ij')

            # Flatten each coordinate grid using the same order as the data
            # This ensures coordinates match the data layout from the binary file
            coordinate_columns = [mesh_grid.ravel(order=page.data_order) for mesh_grid in coordinate_meshgrids]

            # Flatten the data array to match coordinate columns
            # Build list of columns to save: coordinates + data
            columns_to_save = coordinate_columns + [page.data_raw]
            # Add error column if error data is available
            if page.error_raw is not None:
                columns_to_save.append(page.error_raw)

            # Stack columns horizontally and save to file with space-delimited format
            np.savetxt(output_path, np.column_stack(columns_to_save), delimiter=' ', fmt="%g")
        return


class ImageWriter(Writer):
    """Writer responsible for creating PNG images using matplotlib library"""

    def __init__(self, filename, options):
        logger.info("{:s} options:  {:s}".format(repr(self.__class__), repr(options)))
        if not filename.endswith(".png"):
            filename += ".png"
        super().__init__(filename)
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
            zdata = np.squeeze(page.data).T  # (n_x, n_y) -> rows along the vertical axis

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

    def write_single_page(self, page: Page, output_path: Path) -> None:
        """Save the figure of a single page, pages that can't be plotted are skipped"""
        fig = self.get_page_figure(page)
        if not fig:
            return
        import matplotlib.pyplot as plt
        try:
            fig.savefig(output_path)
        except ValueError as e:
            logger.error("Failed to save plot to file: %s", output_path)
            logger.error("Error: %s", e)
            logger.error("Trying to save plot using different font")
            # on some HPC system I get the error
            # "findfont: Generic family 'sans-serif' not found ..."
            # therefore I choose a different font
            plt.rcParams['font.sans-serif'] = ["DejaVu Sans Mono"]
            plt.rcParams['font.family'] = "sans-serif"
            fig.savefig(output_path)
        finally:
            plt.close(fig)
