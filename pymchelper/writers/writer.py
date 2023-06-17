from abc import abstractmethod
import logging
from pathlib import Path
from pymchelper.estimator import Estimator

logger = logging.getLogger(__name__)


class Writer:
    """Base class for all writers."""

    def __init__(self, output_path: str):
        self.output_path = Path(output_path)

    def write(self, estimator: Estimator) -> int:
        """Write the estimator data to a file."""
        # create output directory if it does not exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # save to single page to a file without number (i.e. output.dat)
        if len(estimator.pages) == 1:
            self.write_single_page(page=estimator.pages[0], output_path=self.output_path)
        else:
            # loop over all pages and save an image for each of them
            for i, page in enumerate(estimator.pages):

                # calculate output filename. it will include page number padded with zeros.
                # for 10-99 pages the filename would look like: output_p01.png, ... output_p99.png
                # for 100-999 pages the filename would look like: output_p001.png, ... output_p999.png
                zero_padded_page_no = str(i + 1).zfill(len(str(len(estimator.pages))))
                page_output_path = self.output_path.parent
                page_output_path /= f"{self.output_path.stem}_p{zero_padded_page_no}{self.output_path.suffix}"

                # save the output file
                logger.info("Writing %s", page_output_path)
                self.write_single_page(page=page, output_path=page_output_path)
        return 1

    @abstractmethod
    def write_single_page(self, page, output_path: Path):
        """Write a single page to a file."""
        raise NotImplementedError
