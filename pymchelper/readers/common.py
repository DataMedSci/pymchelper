from abc import abstractmethod
import logging
from typing import Optional, TYPE_CHECKING

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
        return self.read_data(estimator)

    @abstractmethod
    def read_data(self, estimator: 'Estimator') -> bool:
        pass

    @property
    @abstractmethod
    def corename(self) -> Optional[str]:
        pass
