import logging

logger = logging.getLogger(__name__)


class Inspector:
    def __init__(self, filename, options):
        logger.debug("Initialising Inspector writer")
        self.options = options

    def write(self, detector):
        """Print all keys and values from detector structure

        they include also a metadata read from binary output file
        """
        for name, value in sorted(detector.__dict__.items()):
            # be careful not to check for np.array but for np.ndarray!
            if name not in {'data', 'data_raw', 'error', 'error_raw', 'counter'}:  # skip non-metadata fields
                line = "{:24s}: '{:s}'".format(str(name), str(value))
                print(line)
        # print some data-related statistics
        print(75 * "*")
        print("Data min: {:g}, max: {:g}".format(detector.data.min(), detector.data.max()))

        if self.options.details:
            # print data scatter-plot if possible
            if detector.dimension == 1:
                try:
                    from hipsterplot import plot
                    print(75 * "*")
                    print("Data scatter plot")
                    plot(detector.data_raw)
                except ImportError:
                    logger.warning("Detailed summary requires installation of hipsterplot package")
            # print data histogram if possible
            try:
                from bashplotlib.histogram import plot_hist
                print(75 * "*")
                print("Data histogram")
                plot_hist(detector.data_raw, bincount=70, xlab=False, showSummary=True)
            except ImportError:
                logger.warning("Detailed summary requires installation of bashplotlib package")

        return 0
