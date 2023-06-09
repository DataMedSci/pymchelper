import logging
from pathlib import Path

from pymchelper.estimator import Estimator
from pymchelper.page import Page
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.writers.writer import Writer

logger = logging.getLogger(__name__)


class MCPLWriter(Writer):
    def __init__(self, output_path: str, _):
        self.output_path = Path(output_path).with_suffix(".mcpl")

    def write_single_page(self, page: Page, output_path: Path):
        """TODO"""
        logger.info("Writing page to: %s", str(output_path))

        # special case for MCPL data
        if page.dettyp == SHDetType.mcpl:
            output_path.write_bytes(page.data_raw)
            return
