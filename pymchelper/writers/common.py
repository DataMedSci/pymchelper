from enum import IntEnum

from pymchelper.writers.excel import ExcelWriter
from pymchelper.writers.inspector import Inspector
from pymchelper.writers.plots import GnuplotDataWriter, PlotDataWriter, ImageWriter
from pymchelper.writers.shieldhit import TxtWriter
from pymchelper.writers.sparse import SparseWriter
from pymchelper.writers.trip98 import TripCubeWriter, TripDddWriter


class Converters(IntEnum):
    """
    Available converters
    """
    txt = 0
    plotdata = 1
    gnuplot = 2
    image = 3
    tripcube = 4
    tripddd = 5
    excel = 6
    sparse = 7
    inspect = 8

    @classmethod
    def _converter_mapping(cls, item):
        return {
            cls.txt: TxtWriter,
            cls.gnuplot: GnuplotDataWriter,
            cls.plotdata: PlotDataWriter,
            cls.image: ImageWriter,
            cls.tripcube: TripCubeWriter,
            cls.tripddd: TripDddWriter,
            cls.excel: ExcelWriter,
            cls.sparse: SparseWriter,
            cls.inspect: Inspector
        }.get(item)

    @classmethod
    def fromname(cls, name):
        return cls._converter_mapping(Converters[name])

    @classmethod
    def fromnumber(cls, number):
        return cls._converter_mapping[Converters(number)]
