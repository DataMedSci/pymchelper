from enum import IntEnum
import logging

import numpy as np

from pymchelper.readers.common import ReaderFactory
from pymchelper.readers.shieldhit.reader_base import read_next_token
from pymchelper.readers.shieldhit.reader_bdo2016 import SHReaderBDO2016
from pymchelper.readers.shieldhit.reader_bdo2019 import SHReaderBDO2019
from pymchelper.readers.shieldhit.reader_bin2010 import SHReaderBin2010
from pymchelper.readers.shieldhit.binary_spec import SHBDOTagID

logger = logging.getLogger(__name__)


def file_has_sh_magic_number(filename):
    """
    BDO binary files, introduced in 2016 (BDO2016 and BDO2019 formats) starts with 6 magic bytes xSH12A
    :param filename: Binary file filename
    :return: True if binary file starts with SH magic number
    """
    sh_bdo_magic_number = b'xSH12A'
    has_bdo_magic_number = False
    with open(filename, "rb") as f:
        d1 = np.dtype([('magic', 'S6')])  # TODO add a check if file has less than 6 bytes or is empty
        x = np.fromfile(f, dtype=d1, count=1)
        if x:
            # compare first 6 bytes with reference string
            has_bdo_magic_number = (sh_bdo_magic_number == x['magic'][0])

    logger.debug("File {:s} has magic number: {:s}".format(filename, str(has_bdo_magic_number)))
    return has_bdo_magic_number


def extract_sh_ver(filename):
    """
    BDO binary files, introduced in 2016 (BDO2016 and BDO2019 formats) contain information about SH VER
    :param filename: Binary file filename
    :return: SH12 version (as a string, i.e. 0.7) or None if version information was not found in the file
    """

    ver = None
    with open(filename, "rb") as f:
        d1 = np.dtype([('magic', 'S6'),
                       ('end', 'S2'),
                       ('vstr', 'S16')])  # TODO add a check if file has less than 6 bytes or is empty
        x = np.fromfile(f, dtype=d1, count=1)
        logger.debug("File {:s}, raw version info {:s}".format(filename, str(x['vstr'][0])))
        try:
            ver = x['vstr'][0].decode('ASCII')
        except UnicodeDecodeError:
            ver = None

    logger.debug("File {:s}, SH12A version: {:s}".format(filename, str(ver)))
    return ver


class SHFileFormatId(IntEnum):
    """
    SHIELD-HIT12A file format ids, as described in sh_file_format.h file
    """
    bin2010 = 0   # Old binary format from 2010, the first version David wrote back then
    bdo2016 = 1   # year 2016 .bdo file format, now with proper tags, used from SH 0.6.0
    bdo2019 = 2   # year 2019 .bdo style, introduced June 2019
    ascii = 3     # raw text format
    csv = 4       # comma separated file format


def read_token(filename, token_id):
    """
    TODO
    :param filename:
    :param token_id:
    :return:
    """
    with open(filename, "rb") as f:

        # skip ASCII header
        d1 = np.dtype([('magic', 'S6'), ('endiannes', 'S2'), ('vstr', 'S16')])
        np.fromfile(f, dtype=d1, count=1)

        # read tokens from rest of the file
        while f:
            token = read_next_token(f)
            if token is None:
                break
            pl_id, _pl_type, _pl_len, _pl = token
            if pl_id == token_id:

                logger.debug("Read token {:s} (0x{:02x}) value {} type {:s} length {:d}".format(
                    SHBDOTagID(pl_id).name,
                    pl_id,
                    _pl,
                    _pl_type.decode('ASCII'),
                    _pl_len
                ))

                pl = [None] * _pl_len

                # decode all strings (currently there will never be more than one per token)
                if 'S' in _pl_type.decode('ASCII'):
                    for i, _j in enumerate(_pl):
                        pl[i] = _pl[i].decode('ASCII').strip()
                else:
                    pl = _pl

                if len(pl) == 1:
                    pl = pl[0]

                return pl
        return None


class SHReaderFactory(ReaderFactory):
    def get_reader(self):
        """
        Inspect binary file and return appropriate reader object
        :return:
        """
        reader = None

        # TODO add ZIP file unpacking

        # magic number was introduced together with first token-based BDO file format (BDO2016)
        # presence of magic number means we could have BDO2016 or BDO2019 format
        if file_has_sh_magic_number(self.filename):
            reader = SHReaderBDO2019

            # format tag specifying binary standard was introduced in SH12A v0.7.4-dev on  07.06.2019 (commit 6eddf98)
            file_format = read_token(self.filename, SHBDOTagID.format)
            if file_format:
                logger.debug("File format: {} {:s}".format(file_format, SHFileFormatId(file_format).name))
                if file_format == SHFileFormatId.bdo2019:
                    reader = SHReaderBDO2019
                elif file_format == SHFileFormatId.bdo2016:
                    reader = SHReaderBDO2016
                else:
                    print("What shall we do ?")
            else:
                # in case format tag is missing we default to BDO2016 format
                # this mean we cannot read BDO2019 files generated with SH12A built before 07.06.2019
                logger.info("File format information missing (token)")
                reader = SHReaderBDO2016
        else:
            # lack of magic number means we expect Fortran-style binary format (BIN2010)
            reader = SHReaderBin2010

        # ver_short = extract_sh_ver(self.filename)
        # logger.info("Short version: {:s}".format(str(ver_short)))
        # ver_long = read_token(self.filename, SHBDOTagID.shversion)
        # logger.info("Long version: {:s}".format(str(ver_long)))

        return reader


class SHReaderASCII:
    """
    Reads plain text files with data saved by binary-to-ascii converter.
    """

    def __init__(self, filename):
        self.filename = filename

    def read_header(self, detector):
        raise NotImplementedError

    def read_payload(self, detector):
        raise NotImplementedError

    def read(self, detector):
        self.read_header(detector)
        self.read_payload(detector)
