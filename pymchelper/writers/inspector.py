import logging
from pymchelper.estimator import Estimator

logger = logging.getLogger(__name__)


class Inspector:

    def __init__(self, filename, options):
        logger.debug("Initialising Inspector writer")
        self.options = options

    def write(self, estimator: Estimator):
        """Print all keys and values from estimator structure

        they include also a metadata read from binary output file
        """
        for name, value in sorted(estimator.__dict__.items()):
            # skip non-metadata fields
            if name not in {'data', 'data_raw', 'error', 'error_raw', 'counter', 'pages'}:
                line = f"{name:24s}: {value}"
                print(line)
        # print some data-related statistics
        print(75 * "*")

        for page_no, page in enumerate(estimator.pages):
            print("Page {} / {}".format(page_no, len(estimator.pages)))
            for name, value in sorted(page.__dict__.items()):
                # skip non-metadata fields
                if name not in {'data', 'data_raw', 'error', 'error_raw'}:
                    line = f"\t{name:24s}: {value}"
                    print(line)
            print(f"Data min: {page.data.min():g}, max: {page.data.max():g}, mean: {page.data.mean():g}")
            if page.error is not None:
                print(f"Error min: {page.error.min():g}, max: {page.error.max():g}, mean: {page.error.mean():g}")
            else:
                print("No error data")
            print(75 * "-")

        if self.options.details:
            # print data scatter-plot if possible
            if estimator.dimension == 1 and len(self.pages) == 1:
                try:
                    from hipsterplot import plot
                    print(75 * "*")
                    print("Data scatter plot")
                    plot(estimator.data_raw)
                except ImportError:
                    logger.warning("Detailed summary requires installation of hipsterplot package")
            # print data histogram if possible
            try:
                from bashplotlib.histogram import plot_hist
                print(75 * "*")
                print("Data histogram")
                plot_hist(estimator.data_raw, bincount=70, xlab=False, showSummary=True)
            except ImportError:
                logger.warning("Detailed summary requires installation of bashplotlib package")

        return 0
