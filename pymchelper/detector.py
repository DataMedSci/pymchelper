import logging
from collections import namedtuple, defaultdict

import numpy as np

from pymchelper.readers.fluka import FlukaBinaryReader
from pymchelper.readers.shieldhit import SHFortranReader, SHBinaryReader, SHConverters
from pymchelper.shieldhit.detector.detector import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.writers.plots import SHImageWriter, SHGnuplotDataWriter, SHPlotDataWriter
from pymchelper.writers.shieldhit import SHFortranWriter
from pymchelper.writers.trip98 import SHTripCubeWriter

logger = logging.getLogger(__name__)

# !! - DET/IDET list of detector attributes from detect.dat (DET for float)
# !!
# !! - IDET(1) : Number of bins in first dimension. x or r or zones
# !! - IDET(2) : Number of bins in snd dimension, y or theta
# !! - IDET(3) : Number of bins in thrd dimension, z
# !! - IDET(4) : Particle type requested for scoring
# !! - IDET(5) : Detector type (see INITDET)
# !! - IDET(6) : Z of particle to be scored
# !! - IDET(7) : A of particle to be scored (only integers here)
# !! - IDET(8) : Detector material parameter
# !! - IDET(9) : Number of energy/amu (or LET) differential bins,
#                   negative if log.
# !! - IDET(10): Type of differential scoring, either LET, E/amu or polar angle
# !! - IDET(11): Starting zone of scoring for zone scoring
# !!
# !! - DET(1-3): start positions for x y z or r theta z
# !! - DET(4-6): stop positions for x y z or r theta z
# !! - DET(7)  : start differential grid
# !! - DET(8)  : stop differential grid
# !!
# !! - BIN(*)  : 10**8 large array holding results. Accessed using pointers.


class Detector:
    data = None
    nstat = -1

    xmin = float("NaN")
    xmax = float("NaN")
    nx = -1

    ymin = float("NaN")
    ymax = float("NaN")
    ny = -1

    zmin = float("NaN")
    zmax = float("NaN")
    nz = -1

    dettyp = SHDetType.unknown
    geotyp = SHGeoType.unknown
    particle = 0

    # number of files
    counter = -1

    def read(self, filename):
        reader = SHFortranReader(filename)
        if filename.endswith(".bdo"):
            reader = SHBinaryReader(filename)
        # find better way to discover if file comes from Fluka
        elif "_fort" in filename:
            reader = FlukaBinaryReader(filename)
        reader.read(self)
        self.counter = 1

    def append(self, other_detector):
        # TODO add compatibility check
        self.data += other_detector.data
        self.nstat += other_detector.nstat
        self.counter += 1

    def average_with_nan(self, other_detectors):
        # TODO add compatibility check
        l = [det.data for det in other_detectors]
        l.append(self.data)
        self.data = np.nanmean(l, axis=0)
        self.nstat += sum(det.nstat for det in other_detectors)
        self.counter += len(other_detectors)

    def save(self, filename, conv_names=[SHConverters.standard.name], colormap=SHImageWriter.default_colormap):
        _converter_mapping = {
            SHConverters.standard: SHFortranWriter,
            SHConverters.gnuplot: SHGnuplotDataWriter,
            SHConverters.plotdata: SHPlotDataWriter,
            SHConverters.image: SHImageWriter,
            SHConverters.tripcube: SHTripCubeWriter
        }
        for conv_name in conv_names:
            writer = _converter_mapping[SHConverters[conv_name]](filename)
            if SHConverters[conv_name] == SHConverters.image:
                writer.set_colormap(colormap)
            writer.write(self)

    def __str__(self):
        result = ""
        result += "data" + str(self.data[0].shape) + "\n"
        result += "nstat = {:d}\n".format(self.nstat)
        result += "X {:g} - {:g} ({:d} items)\n".format(self.xmin, self.xmax, self.nx)
        result += "Y {:g} - {:g} ({:d} items)\n".format(self.ymin, self.ymax, self.ny)
        result += "Z {:g} - {:g} ({:d} items)\n".format(self.zmin, self.zmax, self.nz)
        result += "dettyp {:s}\n".format(self.dettyp.name)
        result += "counter of files {:d}\n".format(self.counter)
        result += "dimension {:d}\n".format(self.dimension)
        result += "Xs {:d}\n".format(len(list(self.x)))
        result += "Xp {:d}\n".format(len(list(self.axis_values(0, plotting_order=True))))
        result += "Ys {:d}\n".format(len(list(self.y)))
        result += "Yp {:d}\n".format(len(list(self.axis_values(1, plotting_order=True))))
        result += "Zs {:d}\n".format(len(list(self.z)))
        result += "Zp {:d}\n".format(len(list(self.axis_values(2, plotting_order=True))))
        result += "V {:d}\n".format(len(list(self.data)))
        return result

    @staticmethod
    def _running_index_i(p, j_max, k_max):
        return p % k_max

    @staticmethod
    def _running_index_j(p, j_max, k_max):
        return (p // k_max) % j_max

    @staticmethod
    def _running_index_k(p, j_max, k_max):
        return p // (j_max * k_max)

    def _running_indices(self, axis_no):
        if axis_no == 0:
            return self._running_index_i
        elif axis_no == 1:
            return self._running_index_j
        elif axis_no == 2:
            return self._running_index_k
        return None

    @staticmethod
    def _linspace(tmin, tmax, tn, ind):
        dt = (tmax - tmin) / tn
        return tmin + (ind + 0.5) * dt

    def axis_values(self, axis_no, plotting_order=False):
        if plotting_order:
            axis_no = self._axes_plotting_order[axis_no]
        a = self.axis_data(axis_no)
        for p in range(self.nx * self.ny * self.nz):
            ind = self._running_indices(axis_no)(p, self.ny, self.nx)
            yield self._linspace(a.min, a.max, a.n, ind)

    @property
    def x(self):
        return self.axis_values(0)

    @property
    def y(self):
        return self.axis_values(1)

    @property
    def z(self):
        return self.axis_values(2)

    @property
    def v(self):
        return self.data

    AxisData = namedtuple('AxisData', ['min', 'max', 'n'])

    def axis_data(self, axis_number, plotting_order=False):
        if plotting_order:
            axis_number = self._axes_plotting_order[axis_number]
        if axis_number == 0:
            return self.AxisData(min=self.xmin, max=self.xmax, n=self.nx)
        elif axis_number == 1:
            return self.AxisData(min=self.ymin, max=self.ymax, n=self.ny)
        elif axis_number == 2:
            return self.AxisData(min=self.zmin, max=self.zmax, n=self.nz)
        else:
            return None

    @property
    def is_valid(self):
        valid_counters = self.nx > 0 and self.ny > 0 and self.nz > 0
        data_exists = self.data is not None
        borders_correct = self.xmax >= self.xmin and\
            self.ymax >= self.ymin and\
            self.zmax >= self.zmin
        nstat_correct = self.nstat > 0
        return valid_counters and data_exists \
            and borders_correct and nstat_correct

    # 0,1,2,3
    @property
    def dimension(self):
        if self.is_valid:
            return 3 - (self.nx, self.ny, self.nz).count(1)
        else:
            return -1

    @property
    def _axes_plotting_order(self):
        axis_data = list(enumerate((self.nx, self.ny, self.nz)))
        sorted_data = sorted(axis_data, key=lambda x: x[1], reverse=True)
        return tuple(i for i, ax in sorted_data)


def merge_list(input_file_list,
               output_file,
               conv_names=[SHConverters.standard.name],
               nan=False,
               colormap=SHImageWriter.default_colormap):
    first = Detector()
    first.read(input_file_list[0])

    other_detectors = []

    for file in input_file_list[1:]:
        next_one = Detector()
        next_one.read(file)
        if nan:
            other_detectors.append(next_one)
        else:
            first.append(next_one)

    if other_detectors and nan:
        first.average_with_nan(other_detectors)
    else:
        first.data /= np.float64(first.counter)
    first.save(output_file, conv_names, colormap)


def merge_many(input_file_list,
               conv_names=[SHConverters.standard.name],
               nan=False,
               colormap=SHImageWriter.default_colormap):
    core_names_dict = defaultdict(list)
    for name in input_file_list:
        if name.endswith(".bdo"):
            core_name = name[:-4]
            if name[-8:-4].isdigit() and len(name[-8:-4]) == 4:
                core_name = name[:-8]
            core_names_dict[core_name].append(name)
        elif "_fort." in name:
            core_name = name[-2:]
            core_names_dict[core_name].append(name)

    for core_name, group_with_same_core in core_names_dict.items():
        merge_list(group_with_same_core, core_name + ".txt", conv_names, nan, colormap)
