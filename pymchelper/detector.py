from collections import namedtuple, defaultdict
import logging
import os

import numpy as np
from enum import IntEnum

from pymchelper.readers.fluka import FlukaBinaryReader
from pymchelper.readers.shieldhit import SHTextReader, SHBinaryReader
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.writers.excel import ExcelWriter
from pymchelper.writers.plots import ImageWriter, GnuplotDataWriter, PlotDataWriter
from pymchelper.writers.shieldhit import TxtWriter
from pymchelper.writers.sparse import SparseWriter
from pymchelper.writers.trip98 import TripCubeWriter, TripDddWriter

logger = logging.getLogger(__name__)


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


class ErrorEstimate(IntEnum):
    none = 0
    stderr = 1
    stddev = 2


class Axis(IntEnum):
    """
    Axis numbers
    """
    x = 0
    y = 1
    z = 2


_converter_mapping = {
    Converters.txt: TxtWriter,
    Converters.gnuplot: GnuplotDataWriter,
    Converters.plotdata: PlotDataWriter,
    Converters.image: ImageWriter,
    Converters.tripcube: TripCubeWriter,
    Converters.tripddd: TripDddWriter,
    Converters.excel: ExcelWriter,
    Converters.sparse: SparseWriter
}


class Detector:
    """
    Holds data read from single estimator
    """
    data = None
    error = None

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

    _M2 = None  # accumulator needed by average_with_other method

    def read(self, filename, nscale=1):
        """
        Reads binary file with. Automatically discovers which reader should be used.
        :param filename: binary file name
        :param nscale:
        :return: none
        """
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
        reader.read(self, nscale)
        self.counter = 1

    def average_with_nan(self, other_detectors, error_estimate=ErrorEstimate.stderr):
        """
        Average (not add) data with other detector, excluding malformed data (NaN) from averaging.
        :param other_detectors:
        :param error_estimate:
        :return:
        """
        # TODO add compatibility check
        _l = [det.data for det in other_detectors]
        _l.append(self.data)
        self.counter += len(other_detectors)
        self.nstat += sum(det.nstat for det in other_detectors)
        self.data = np.nanmean(_l, axis=0)
        if error_estimate != ErrorEstimate.none:
            # s = stddev = sqrt(1/(n-1)sum(x-<x>)**2)
            # s : corrected sample standard deviation
            self.error = np.nanstd(_l, axis=0, ddof=1)

    def average_with_other(self, other_detector, error_estimate=ErrorEstimate.stderr):
        """
        Average (not add) data with other detector
        :param other_detector:
        :param error_estimate:
        :return:
        """

        # Running variance algorithm based on algorithm by B. P. Welford,
        # presented in Donald Knuth's Art of Computer Programming, Vol 2, page 232, 3rd edition.
        # Can be found here: http://www.johndcook.com/blog/standard_deviation/
        # and https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Online_algorithm
        self.counter += 1
        self.nstat += other_detector.nstat
        delta = other_detector.data - self.data                    # delta = x - mean
        self.data += delta / self.counter                          # mean += delta / n
        if error_estimate != ErrorEstimate.none:
            self._M2 += delta * (other_detector.data - self.data)  # M2 += delta * (x - mean)

            # unbiased sample variance is stored in `self._M2 / (self.counter - 1)`
            # unbiased sample standard deviation in classical algorithm is calculated as (sqrt(1/(n-1)sum(x-<x>)**2)
            # here it is calculated as square root of unbiased sample variance:
            self.error = np.sqrt(self._M2 / (self.counter - 1))

    def save(self, filename, options):
        """
        Save data to the file, using list of converters
        :param filename:
        :param options:
        :return:
        """
        writer = _converter_mapping[Converters[options.command]](filename, options)
        logger.info("Writing file with corename {:s}".format(filename))
        writer.write(self)

    def __str__(self):
        result = ""
        result += "data" + str(self.data[0].shape) + "\n"
        if self.error is not None:
            result += "error" + str(self.error[0].shape) + "\n"
        result += "nstat = {:d}\n".format(self.nstat)
        result += "X {:g} - {:g} ({:d} items)\n".format(self.xmin, self.xmax, self.nx)
        result += "Y {:g} - {:g} ({:d} items)\n".format(self.ymin, self.ymax, self.ny)
        result += "Z {:g} - {:g} ({:d} items)\n".format(self.zmin, self.zmax, self.nz)
        result += "dettyp {:s}\n".format(self.dettyp.name)
        result += "counter of files {:d}\n".format(self.counter)
        result += "dimension {:d}\n".format(self.dimension)
        result += "Xs {:d}\n".format(len(list(self.x)))
        result += "Xp {:d}\n".format(len(list(self.axis_values(Axis.x, plotting_order=True))))
        result += "Ys {:d}\n".format(len(list(self.y)))
        result += "Yp {:d}\n".format(len(list(self.axis_values(Axis.y, plotting_order=True))))
        result += "Zs {:d}\n".format(len(list(self.z)))
        result += "Zp {:d}\n".format(len(list(self.axis_values(Axis.z, plotting_order=True))))
        result += "V {:d}\n".format(len(list(self.data)))
        return result

    @staticmethod
    def _running_index_i(p, _, k_max):
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
        return self.axis_values(Axis.x)

    @property
    def y(self):
        return self.axis_values(Axis.y)

    @property
    def z(self):
        return self.axis_values(Axis.z)

    @property
    def v(self):
        return self.data

    @property
    def e(self):
        return self.error

    AxisData = namedtuple('AxisData', ['min', 'max', 'n', 'number'])

    def axis_data(self, axis_number, plotting_order=False):
        if plotting_order:
            axis_number = self._axes_plotting_order[axis_number]
        if axis_number == Axis.x:
            return self.AxisData(min=self.xmin, max=self.xmax, n=self.nx, number=axis_number)
        elif axis_number == Axis.y:
            return self.AxisData(min=self.ymin, max=self.ymax, n=self.ny, number=axis_number)
        elif axis_number == Axis.z:
            return self.AxisData(min=self.zmin, max=self.zmax, n=self.nz, number=axis_number)
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
        return valid_counters and data_exists and borders_correct and nstat_correct

    # 0,1,2,3
    @property
    def dimension(self):
        if self.is_valid:
            return 3 - (self.nx, self.ny, self.nz).count(1)
        else:
            return -1

    @property
    def _axes_plotting_order(self):
        result = (Axis.x, Axis.y, Axis.z)
        if self.dimension == 1:
            if self.nx > 1:
                result = (Axis.x, Axis.y, Axis.z)  # X variable; Y,Z constant
            elif self.ny > 1:
                result = (Axis.y, Axis.x, Axis.z)  # Y variable; X,Z constant
            elif self.nz > 1:
                result = (Axis.z, Axis.x, Axis.y)  # Z variable; X,Y constant
        elif self.dimension == 2:
            if self.nx == 1:
                result = (Axis.y, Axis.z, Axis.x)  # Y,Z variable; X constant
            elif self.ny == 1:
                result = (Axis.x, Axis.z, Axis.y)  # X,Z variable; Y constant
            elif self.nz == 1:
                result = (Axis.x, Axis.y, Axis.z)  # X,Y variable; Z constant
        return result


def merge_list(input_file_list,
               output_file,
               options):
    """
    Takes set of input file names, containing data from the same estimator.
    All input files are read and data is filled (and summed) into detector structure.
    Finally data stored in detector is averaged and saved to output file.
    :param input_file_list: list of input files
    :param output_file: name of output file
    :param options: list of parsed options
    :return: none
    """
    first = Detector()
    first.read(input_file_list[0], options.nscale)

    other_detectors = []

    # allocate memory for accumulator needed in standard deviation calculation
    # not needed if:
    #  - averaging is done ignoring NaNs (then numpy nanvar function is used)
    #  - processing only one file
    #  - user requested not to include errors
    if not options.nan and len(input_file_list) > 1 and options.error != ErrorEstimate.none:
        first._M2 = np.zeros_like(first.data)

    # set errors to zero also if reading single file
    if options.error != ErrorEstimate.none:
        first.error = np.zeros_like(first.data)

    # loop over second and next files, if present
    for file in input_file_list[1:]:
        next_one = Detector()
        next_one.read(file, options.nscale)
        if options.nan:
            other_detectors.append(next_one)  # read all detector files into memory
        else:
            first.average_with_other(other_detector=next_one, error_estimate=options.error)

    # user requested averaging ignoring nan and more than one file are present
    if other_detectors and options.nan:
        first.average_with_nan(other_detectors, error_estimate=options.error)

    # up to now first.error stores standard deviation
    # if user requested standard error then we calculate it as:
    # S = stderr = stddev / sqrt(n), or in other words,
    # S = s/sqrt(N) where S is the corrected standard deviation of the mean.
    if len(input_file_list) > 1 and options.error == ErrorEstimate.stderr:
        first.error /= np.sqrt(first.counter)  # np.sqrt() always returns np.float64

    if output_file is None:
        output_file = input_file_list[0][:-4]

    output_dir = os.path.dirname(output_file)
    if output_dir:  # output directory has been found, output_file is not a plain file in current dir
        if not os.path.exists(output_dir):  # directory doesn't exists
            os.makedirs(output_dir)  # let us create it
    first.save(output_file, options)


def _process_one_group(core_name, group_with_same_core, outputdir, options):
    core_dirname, core_basename = os.path.split(core_name)
    if outputdir is None:
        output_file = os.path.join(core_dirname, core_basename)
    else:
        output_file = os.path.join(outputdir, core_basename)
    logger.debug("Setting output core name " + output_file)
    merge_list(group_with_same_core, output_file, options)


def merge_many(input_file_list,
               outputdir,
               options,
               jobs):
    """
    Takes set of input file names, belonging to possibly different estimators.
    Input files are grouped according to the estimators and for each group
    merging is performed, as in @merge_list method.
    Output file name is automatically generated.
    :param input_file_list: list of input files
    :param outputdir: output directory
    :param options: list of parsed options
    :param jobs: number of CPU cores to use (-1 means all)
    :return: none
    """
    core_names_dict = defaultdict(list)
    # keys - core_name, value - list of full paths to corresponding files

    # loop over input list of file paths
    for filepath in input_file_list:

        # extract basename for inspection
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

    # parallel execution of output file generation, using all CPU cores
    # see http://pythonhosted.org/joblib
    try:
        from joblib import Parallel, delayed
        logger.info("Parallel processing on {:d} jobs (-1 means all)".format(jobs))
        # options.verbose count the number of `-v` switches provided by user
        # joblib Parallel class expects the verbosity as a larger number (i.e. multiple of 10)
        worker = Parallel(n_jobs=jobs, verbose=options.verbose * 10)
        worker(
            delayed(_process_one_group)(core_name, group_with_same_core, outputdir, options)
            for core_name, group_with_same_core in core_names_dict.items()
        )
    except (ImportError, SyntaxError):
        # single-cpu implementation, in case joblib library fails (i.e. Python 3.2)
        logger.info("Single CPU processing")
        for core_name, group_with_same_core in core_names_dict.items():
            _process_one_group(core_name, group_with_same_core, outputdir, options)
