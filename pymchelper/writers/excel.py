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

    def write(self, detector):

        try:
            import xlwt
        except ImportError as e:
            logger.error("Generating Excel files not available on your platform (you are probably running Python 3.2).")
            raise e

        # save only 1-D data
        if detector.dimension != 1:
            logger.warning("Detector dimension {:d} different than 1, XLS output not supported".format(
                detector.dimension))
            return

        # create workbook with single sheet
        wb = xlwt.Workbook()
        ws = wb.add_sheet('Data')

        # save X axis data
        for i, x in enumerate(detector.axis_values(0, plotting_order=True)):
            ws.write(i, 0, x)

        # save Y axis data
        for i, y in enumerate(detector.data):
            ws.write(i, 1, y)

        # save error column (if present)
        if np.any(detector.error):
            for i, e in enumerate(detector.error):
                ws.write(i, 2, e)

        # save file
        wb.save(self.filename)
