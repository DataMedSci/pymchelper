import logging

import numpy as np

logger = logging.getLogger(__name__)


class ExcelWriter:
    """
    Supports writing XLS files (MS Excel 2003 format)
    """
    def __init__(self, filename, options):
        self.filename = filename
        if not self.filename.endswith(".xls"):
            self.filename += ".xls"

    def write(self, estimator):
        if len(estimator.pages) > 1:
            print("Conversion of data with multiple pages not supported yet")
            return False

        try:
            import xlwt
        except ImportError as e:
            logger.error("Generating Excel files not available on your platform (you are probably running Python 3.2).")
            raise e

        page = estimator.pages[0]

        # save only 1-D data
        if page.dimension != 1:
            logger.warning("page dimension {:d} != 1, XLS output not supported".format(estimator.dimension))
            return 1

        # create workbook with single sheet
        wb = xlwt.Workbook()
        ws = wb.add_sheet('Data')

        # save X axis data
        for i, x in enumerate(page.plot_axis(0).data):
            ws.write(i, 0, x)

        # save Y axis data
        for i, y in enumerate(page.data_raw):
            ws.write(i, 1, y)

        # save error column (if present)
        if np.all(np.isfinite(page.error_raw)):
            for i, e in enumerate(page.error_raw):
                ws.write(i, 2, e)

        # save file
        logger.info("Writing: " + self.filename)
        wb.save(self.filename)

        return 0
