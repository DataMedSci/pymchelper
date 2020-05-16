from abc import abstractmethod
from collections import defaultdict
import logging
import os

logger = logging.getLogger(__name__)


class ReaderFactory:
    def __init__(self, filename):
        self.filename = filename

    @abstractmethod
    def get_reader(self):
        pass


class Reader:
    def __init__(self, filename):
        self.filename = filename

    @abstractmethod
    def read(self, detector):
        pass

    @property
    @abstractmethod
    def corename(self):
        pass

