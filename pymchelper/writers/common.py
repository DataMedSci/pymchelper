from enum import IntEnum

from pymchelper.writers.excel import ExcelWriter
from pymchelper.writers.inspector import Inspector
from pymchelper.writers.plots import PlotDataWriter, ImageWriter
from pymchelper.writers.shieldhit import TxtWriter
from pymchelper.writers.sparse import SparseWriter
from pymchelper.writers.trip98cube import TRiP98CubeWriter
from pymchelper.writers.trip98ddd import TRiP98DDDWriter
from pymchelper.writers.hdf import HdfWriter
from pymchelper.writers.dicom import DicomWriter

class Converters(IntEnum):
    """
    Available converters
    """
    txt = 0
    plotdata = 1
    image = 3
    tripcube = 4
    tripddd = 5
    excel = 6
    sparse = 7
    inspect = 8
    hdf = 9
    dicom = 10

    @classmethod
    def _converter_mapping(cls, item):
        return {
            cls.txt: TxtWriter,
            cls.plotdata: PlotDataWriter,
            cls.image: ImageWriter,
            cls.tripcube: TRiP98CubeWriter,
            cls.tripddd: TRiP98DDDWriter,
            cls.excel: ExcelWriter,
            cls.sparse: SparseWriter,
            cls.inspect: Inspector,
            cls.hdf: HdfWriter,
            cls.dicom: DicomWriter
        }.get(item)

    @classmethod
    def fromname(cls, name : str):
        return cls._converter_mapping(Converters[name])

    @classmethod
    def fromnumber(cls, number : int):
        return cls._converter_mapping[Converters(number)]
