from collections import defaultdict
from enum import IntEnum
import logging
import os

from pymchelper.readers.fluka import FlukaBinaryReader
from pymchelper.readers.shieldhit import SHBinaryReader, SHTextReader


logger = logging.getLogger(__name__)


class Readers(IntEnum):
    """
    Available converters
    """
    fluka_bin = 0
    shieldhit_bin = 1
    fluka_txt = 2  # TODO to be implemented
    shieldhit_txt = 3

    @property
    @classmethod
    def _readers_mapping(cls):
        return {
            cls.fluka_bin: FlukaBinaryReader,
            cls.shieldhit_bin: SHBinaryReader,
            cls.shieldhit_txt: SHTextReader
        }

    @classmethod
    def fromname(cls, name):
        return cls._readers_mapping[Readers[name]]

    @classmethod
    def fromnumber(cls, number):
        return cls._readers_mapping[Readers(number)]


def guess_reader(filename):
    reader = SHTextReader(filename)

    # check if binary file is generated with SHIELD-HIT12A version > 0.6
    #  (in that case it may or may not have .bdo extension)
    # this check will also pass is file is generated with older SHIELD-HIT12A version
    #  (in that case we rely on the file extension)
    if SHBinaryReader(filename).test_version_0p6() or filename.endswith((".bdo", ".bdox")):
        reader = SHBinaryReader(filename)
    # find better way to discover if file comes from Fluka
    elif "_fort" in filename:
        reader = FlukaBinaryReader(filename)

    return reader


def group_input_files(input_file_list):
    """
    Takes set of input file names, belonging to possibly different estimators.
    Input files are grouped according to the estimators and for each group
    merging is performed, as in @merge_list method.
    Output file name is automatically generated.
    :param input_file_list: list of input files
    :return: core_names_dict
    """
    core_names_dict = defaultdict(list)
    # keys - core_name, value - list of full paths to corresponding files

    # loop over input list of file paths
    for filepath in input_file_list:

        # extract basename (strip directory part) for inspection
        basename = os.path.basename(filepath)

        # SHIELD-HIT12A binary file encountered
        if SHBinaryReader(filepath).test_version_0p6() or filepath.endswith(('.bdo', '.bdox')):
            # we expect the basename to follow one of two conventions:
            #  - corenameABCD.bdo (where ABCD is 4-digit integer)
            #  - corename.bdo
            core_name = basename[:-4]  # assume no number in the basename
            if basename[-8:-4].isdigit() and len(basename[-8:-4]) == 4:  # check if number present
                core_name = basename[:-8]
            core_names_dict[core_name].append(filepath)
        elif "_fort." in filepath:  # Fluka binary file encountered
            core_name = filepath[-2:]
            core_names_dict[core_name].append(filepath)

    return core_names_dict
