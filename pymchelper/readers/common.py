from abc import abstractmethod
import logging

logger = logging.getLogger(__name__)


class ReaderFactory(object):

    def __init__(self, filename):
        self.filename = filename

    @abstractmethod
    def get_reader(self):
        pass


class Reader(object):

    def __init__(self, filename):
        self.filename = filename

    def read(self, estimator):
        result = self.read_data(estimator)
        if not result:
            return False
        for page in estimator.pages:
            page.error_raw = None
        return True

    @abstractmethod
    def read_data(self, estimator):
        pass

    @property
    @abstractmethod
    def corename(self):
        pass
