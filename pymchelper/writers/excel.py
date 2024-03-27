import logging

from pymchelper.estimator import Estimator

logger = logging.getLogger(__name__)


class ExcelWriter:
    """
    Supports writing XLS files (MS Excel 2003 format)
    """

    def __init__(self, filename, options):
        self.filename = filename
        if not self.filename.endswith(".xls"):
            self.filename += ".xls"

    def write(self, estimator: Estimator):
        try:
            import xlwt
        except ImportError as e:
            logger.error("Generating Excel files not available on your platform (please install xlwt).")
            raise e

        # create workbook
        wb = xlwt.Workbook()

        for page_id, page in enumerate(estimator.pages):

            # save only 1-D data
            if page.dimension != 1:
                logger.warning("page dimension {:d} != 1, XLS output not supported".format(estimator.dimension))
                return 1

            # create worksheet
            ws = wb.add_sheet(f'Data_p{page_id}')

            # save X axis data
            for i, x in enumerate(page.plot_axis(0).data):
                ws.write(i, 0, x)

            # save Y axis data
            for i, y in enumerate(page.data_raw):
                ws.write(i, 1, y)

            # save error column (if present)
            if page.error_raw is not None:
                for i, e in enumerate(page.error_raw):
                    ws.write(i, 2, e)

        # save file
        logger.info("Writing: " + self.filename)
        wb.save(self.filename)

        return 0
