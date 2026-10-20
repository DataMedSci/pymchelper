from abc import abstractmethod
import logging
from typing import Optional, TYPE_CHECKING

from pymchelper.shieldhit.detector.detector_type import SHDetType

if TYPE_CHECKING:
    from pymchelper.estimator import Estimator

logger = logging.getLogger(__name__)


class ReaderFactory(object):

    def __init__(self, filename: str) -> None:
        self.filename: str = filename

    @abstractmethod
    def get_reader(self):
        pass


class Reader(object):

    def __init__(self, filename: str) -> None:
        self.filename: str = filename

    def read(self, estimator: 'Estimator') -> bool:
        result = self.read_data(estimator)
        if not result:
            return False
        for page in estimator.pages:
            page.error_raw = None
        _check_page_sizes(estimator, self.filename)
        return True

    @abstractmethod
    def read_data(self, estimator: 'Estimator') -> bool:
        pass

    @property
    @abstractmethod
    def corename(self) -> Optional[str]:
        pass


def _check_page_sizes(estimator: 'Estimator', filename: str) -> None:
    """
    Raise ValueError if the estimator has no pages or a page holds a different number of values than its mesh.
    Phase space (MCPL) pages have no mesh, they only need a multiple of 8 values, one 8-value row per particle.
    """
    if not estimator.pages:
        raise ValueError(f"{filename}: no pages, the file is truncated or corrupted")
    for page in estimator.pages:
        if page.dettyp == SHDetType.mcpl:
            if page.data_raw.size % 8 != 0:
                raise ValueError(f"{filename}: page {page.name} holds {page.data_raw.size} values, "
                                 "not a multiple of 8, the file is truncated or corrupted")
            continue

        expected_size = estimator.x.n * estimator.y.n * estimator.z.n * page.diff_axis1.n * page.diff_axis2.n
        if page.data_raw.size != expected_size:
            raise ValueError(f"{filename}: page {page.name} holds {page.data_raw.size} values "
                             f"instead of {expected_size}, the file is truncated or corrupted")
