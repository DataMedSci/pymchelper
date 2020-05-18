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

    @abstractmethod
    def read(self, detector):
        pass

    @property
    @abstractmethod
    def corename(self):
        pass
