#!/usr/bin/env python

import sys
import argparse
import glob
from collections import namedtuple, defaultdict
from enum import IntEnum

import numpy as np


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


class SHConverters(IntEnum):
    standard = 0
    plotdata = 1
    gnuplot = 2
    image = 3
    tripcube = 4


class SHBinaryReader:
    def __init__(self, filename):
        self.filename = filename

    def read_header(self, detector):
        print("Reading header:", self.filename)
        # effective read
        # first figure out the length.
        header_dtype = np.dtype([('fo1', '<i4'),
                                 ('geotyp', 'S10'),
                                 ('fo2', '<i4'),
                                 ('fo3', '<i4'),
                                 ('nstat', '<i4'),
                                 ('fo4', '<i4'),
                                 ('fo5', '<i4'),
                                 ('det', ('<f8', 8)),
                                 ('fo6', '<i4'),
                                 ('fo7', '<i4'),
                                 ('idet', ('<i4'), 11),
                                 ('fo8', '<i4'),
                                 ('reclen', '<i4')])
        header = np.fromfile(self.filename, header_dtype, count=1)
        detector.rec_size = header['reclen'][0] // 8

        idet = header['idet']

        detector.nx = idet[0][0]
        detector.ny = idet[0][1]
        detector.nz = idet[0][2]

        detector.det = header['det']
        detector.particle = idet[0][3]

        try:
            detector.geotyp = SHGeoType[
                header['geotyp'][0].decode('ascii').strip().lower()
            ]
        except Exception:
            detector.geotyp = SHGeoType.unknown
        detector.nstat = header['nstat'][0]

        detector.xmin = header['det'][0][0]
        detector.ymin = header['det'][0][1]
        detector.zmin = header['det'][0][2]

        detector.xmax = header['det'][0][3]
        detector.ymax = header['det'][0][4]
        detector.zmax = header['det'][0][5]

        detector.dettyp = SHDetType(idet[0][4])

    def read_payload(self, detector):
        print("Reading data:", self.filename)

        if detector.geotyp == SHGeoType.unknown \
                or detector.dettyp == SHDetType.unknown:
            detector.data = []
            return

        # next read the data:
        record_dtype = np.dtype([
            ('trash', ('S158')), ('bin2', ('<f8'), detector.rec_size)
        ])
        record = np.fromfile(self.filename, record_dtype, count=-1)
        detector.data = record['bin2'][:][0]
        if detector.dimension == 0:
            detector.data = np.asarray([detector.data])

        # normalize result if we need that.
        if detector.dettyp not in (SHDetType.dlet, SHDetType.tlet,
                                   SHDetType.avg_energy, SHDetType.avg_beta,
                                   SHDetType.material):
            detector.data /= np.float64(detector.nstat)

        detector.counter = 1

    def read(self, detector):
        self.read_header(detector)
        self.read_payload(detector)


class SHUniverseReader:
    def __init__(self, filename):
        self.filename = filename

    def read(self, detector):
        detector.counter = 1.0

        detector.tmpdata = np.loadtxt(self.filename)

        tmpx = detector.tmpdata[:, 0]
        tmpy = detector.tmpdata[:, 1]
        tmpz = detector.tmpdata[:, 2]
        tmpv = detector.tmpdata[:, 3]

        detector.nx = np.unique(tmpx).size
        detector.ny = np.unique(tmpy).size
        detector.nz = np.unique(tmpz).size

        detector.det = "GGEN"
        detector.particle = 0

        detector.geotyp = SHGeoType.unknown
        detector.nstat = 1

        if tmpx.max() > tmpx.min():
            dx = (tmpx.max() - tmpx.min()) / (detector.nx - 1)
        else:
            dx = 0

        if tmpy.max() > tmpy.min():
            dy = (tmpy.max() - tmpy.min()) / (detector.ny - 1)
        else:
            dy = 0

        if tmpz.max() > tmpz.min():
            dz = (tmpz.max() - tmpz.min()) / (detector.nz - 1)
        else:
            dz = 0

        detector.xmin = tmpx.min() - dx / 2.0
        detector.ymin = tmpy.min() - dy / 2.0
        detector.zmin = tmpz.min() - dz / 2.0

        detector.xmax = tmpx.max() + dx / 2.0
        detector.ymax = tmpy.max() + dy / 2.0
        detector.zmax = tmpz.max() + dz / 2.0

        detector.dettyp = SHDetType.unknown

        detector.data = tmpv


class SHFortranReader:
    def __init__(self, filename):
        self.filename = filename

    def read_header(self, detector):
        # TODO
        pass

    def read_payload(self, detector):
        # TODO
        pass

    def read(self, detector):
        self.read_header(detector)
        self.read_payload(detector)


class FlukaBinaryReader:
    def __init__(self, filename):
        self.filename = filename

    def read(self, detector):
        from pymchelper.flair.Data import Usrbin, unpackArray
        usr = Usrbin(self.filename)
        usr.say()  # file,title,time,weight,ncase,nbatch
        for i in range(len(usr.detector)):
            print("-" * 20, "Detector number %i" % i, "-" * 20)
            usr.say(i)  # details for each detector
        data = usr.readData(0)
        print("len(data):", len(data))
        fdata = unpackArray(data)
        print("len(fdata):", len(fdata))

        # TODO read detector type
        detector.det = "FLUKA"

        # TODO read particle type
        detector.particle = 0

        # TODO read geo type
        detector.geotyp = SHGeoType.unknown

        # TODO cross-check statistics
        detector.nstat = usr.ncase

        # TODO figure out when more detectors are used
        detector.nx = usr.detector[0].nx
        detector.ny = usr.detector[0].ny
        detector.nz = usr.detector[0].nz

        detector.xmin = usr.detector[0].xlow
        detector.ymin = usr.detector[0].ylow
        detector.zmin = usr.detector[0].zlow

        detector.xmax = usr.detector[0].xhigh
        detector.ymax = usr.detector[0].yhigh
        detector.zmax = usr.detector[0].zhigh

        # TODO read detector type
        detector.dettyp = SHDetType.unknown

        detector.data = fdata


class SHBinaryWriter:
    def __init__(self, filename):
        self.filename = filename

    def write(self, detector):
        # TODO
        pass


class SHFortranWriter:
    @staticmethod
    def _axis_name(geo_type, axis_no):
        cyl = ['R', 'PHI', 'Z']
        msh = ['X', 'Y', 'Z']
        if geo_type in (SHGeoType.cyl, SHGeoType.dcyl):
            return cyl[axis_no]
        else:
            return msh[axis_no]

    def __init__(self, filename):
        self.filename = filename

    def write(self, det):
        from pymchelper.fortranformatter import format_d, format_e
        header = "#   DETECTOR OUTPUT\n"
        ax = self._axis_name(det.geotyp, 0)
        ay = self._axis_name(det.geotyp, 1)
        az = self._axis_name(det.geotyp, 2)
        header += "#   {:s} BIN:{:6d} {:s} BIN:{:6d} {:s} BIN:{:6d}\n".format(
            ax, det.nx, ay, det.ny, az, det.nz)
        header += "#   JPART:{:6d} DETECTOR TYPE:{:s}\n".format(
            det.particle, str(det.dettyp).ljust(10))
        header += "#   {:s} START:{:s}".format(ax, format_d(10, 3, det.xmin))
        header += " {:s} START:{:s}".format(ay, format_d(10, 3, det.ymin))
        header += " {:s} START:{:s}\n".format(az, format_d(10, 3, det.zmin))
        header += "#   {:s} END  :{:s}".format(ax, format_d(10, 3, det.xmax))
        header += " {:s} END  :{:s}".format(ay, format_d(10, 3, det.ymax))
        header += " {:s} END  :{:s}\n".format(az, format_d(10, 3, det.zmax))
        header += "#   PRIMARIES:" + format_d(10, 3, det.nstat) + "\n"
        with open(self.filename, 'w') as fout:
            print("Writing: " + self.filename)
            fout.write(header)
            for x, y, z, v in zip(det.x, det.y, det.z, det.data):
                x = float('nan') if np.isnan(x) else x
                y = float('nan') if np.isnan(y) else y
                z = float('nan') if np.isnan(z) else z
                v = float('nan') if np.isnan(v) else v
                tmp = format_e(14, 7, x) + " " + \
                    format_e(14, 7, y) + " " + \
                    format_e(14, 7, z) + " " + \
                    format_e(23, 16, v) + "\n"
                fout.write(tmp)


class SHPlotDataWriter:
    def __init__(self, filename):
        self.filename = filename + ".dat"

    def write(self, detector):
        print("Writing: " + self.filename)
        axis_values = [list(detector.axis_values(i, plotting_order=True))
                       for i in range(detector.dimension)]
        fmt = "%g" + " %g" * detector.dimension
        data = np.transpose(axis_values + [detector.data])
        np.savetxt(self.filename, data, fmt=fmt, delimiter=' ')


class SHGnuplotDataWriter:
    def __init__(self, filename):
        self.data_filename = filename + ".dat"
        self.script_filename = filename + ".plot"
        self.plot_filename = filename + ".png"

    header = """set term png
set output \"{plot_filename}\"
"""

    plotting_command = {
        1: """plot './{data_filename}' w l
        """,
        2: """set pm3d interpolate 0,0
set view map
set dgrid3d
splot '{data_filename}' with pm3d
"""
    }

    def write(self, detector):
        if detector.dimension in (1, 2):
            with open(self.script_filename, 'w') as script_file:
                print("Writing: " + self.script_filename)
                script_file.write(
                    self.header.format(plot_filename=self.plot_filename))
                plt_cmd = self.plotting_command[detector.dimension]
                script_file.write(
                    plt_cmd.format(data_filename=self.data_filename))


class SHImageWriter:
    def __init__(self, filename):
        self.plot_filename = filename + ".png"
        self.colormap = SHImageWriter.default_colormap

    default_colormap = 'gnuplot2'

    def set_colormap(self, colormap):
        self.colormap = colormap

    def write(self, detector):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        xdata = detector.axis_values(0, plotting_order=True)

        if detector.dimension in (1, 2):
            print("Writing: " + self.plot_filename)
            if detector.dimension == 1:
                plt.plot(list(xdata), detector.v)
            elif detector.dimension == 2:
                ydata = detector.axis_values(1, plotting_order=True)

                xn = detector.axis_data(0, plotting_order=True).n
                yn = detector.axis_data(1, plotting_order=True).n

                xlist = np.asarray(list(xdata)).reshape(xn, yn)
                ylist = np.asarray(list(ydata)).reshape(xn, yn)
                zlist = detector.v.reshape(xn, yn)

                plt.pcolormesh(xlist, ylist, zlist, cmap=self.colormap)
                plt.colorbar()
            plt.savefig(self.plot_filename)
            plt.close()


class SHTripCubeWriter:
    def __init__(self, filename):
        self.output_corename = filename

    def write(self, detector):
        from pytrip import dos
        cube = dos.DosCube()
        pixel_size_x = (detector.xmax - detector.xmin) / detector.nx
        pixel_size_z = (detector.zmax - detector.zmin) / detector.nz
        cube.create_empty_cube(1.0,
                               detector.nx,
                               detector.ny,
                               detector.ny,
                               pixel_size=pixel_size_x,
                               slice_distance=pixel_size_z)
        cube.cube = detector.data.reshape(detector.nx,
                                          detector.ny,
                                          detector.nz)
        cube.write(self.output_corename)


class SHDetType(IntEnum):
    unknown = 0
    energy = 1
    fluence = 2
    crossflu = 3
    letflu = 4
    dose = 5
    dlet = 6
    tlet = 7
    avg_energy = 8
    avg_beta = 9
    material = 10
    alanine = 13
    counter = 14
    pet = 15
    dletg = 16
    tletg = 17

    def __str__(self):
        return self.name.upper().replace('_', '-')


class SHGeoType(IntEnum):
    unknown = 0
    zone = 1
    cyl = 2
    msh = 3
    plane = 4
    dzone = 5
    dcyl = 6
    dmsh = 7
    dplane = 8
    dcylz = 10
    dmshz = 11
    trace = 13
    voxscore = 14

    def __str__(self):
        return self.name.upper()


class SHDetect:
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
        elif filename.endswith("universe_zone.dat"):
            reader = SHUniverseReader(filename)
        elif filename.endswith("universe_medium.dat"):
            reader = SHUniverseReader(filename)
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

    def save(self, filename, conv_names=[SHConverters.standard.name],
             colormap=SHImageWriter.default_colormap):
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
        result += "X {:g} - {:g} ({:d} items)\n".format(
            self.xmin, self.xmax, self.nx)
        result += "Y {:g} - {:g} ({:d} items)\n".format(
            self.ymin, self.ymax, self.ny)
        result += "Z {:g} - {:g} ({:d} items)\n".format(
            self.zmin, self.zmax, self.nz)
        result += "dettyp {:s}\n".format(self.dettyp.name)
        result += "counter of files {:d}\n".format(self.counter)
        result += "dimension {:d}\n".format(self.dimension)
        result += "Xs {:d}\n".format(len(list(self.x)))
        result += "Xp {:d}\n".format(
            len(list(self.axis_values(0, plotting_order=True))))
        result += "Ys {:d}\n".format(len(list(self.y)))
        result += "Yp {:d}\n".format(
            len(list(self.axis_values(1, plotting_order=True))))
        result += "Zs {:d}\n".format(len(list(self.z)))
        result += "Zp {:d}\n".format(
            len(list(self.axis_values(2, plotting_order=True))))
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
        borders_correct = self.xmax >= self.xmin \
            and self.ymax >= self.ymin \
            and self.zmax >= self.zmin
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


def merge_list(input_file_list, output_file,
               conv_names=[SHConverters.standard.name],
               nan=False,
               colormap=SHImageWriter.default_colormap):
    first = SHDetect()
    first.read(input_file_list[0])

    other_detectors = []

    for file in input_file_list[1:]:
        next_one = SHDetect()
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
    for core_name, group_with_same_core in core_names_dict.items():
        merge_list(group_with_same_core, core_name + ".txt",
                   conv_names, nan, colormap)


def main(args=sys.argv[1:]):
    import pymchelper
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile",
                        help='input filename, file list or pattern', type=str)
    parser.add_argument("outputfile",
                        help='output filename', nargs='?')
    parser.add_argument("--many",
                        help='automatically merge data from various sources',
                        action="store_true")
    parser.add_argument("--nan",
                        help='ignore NaN in averaging',
                        action="store_true")
    parser.add_argument("--converter",
                        help='converters',
                        default=[SHConverters.standard.name],
                        choices=SHConverters.__members__.keys(), nargs='+')
    parser.add_argument("--colormap",
                        help='color map for image converter',
                        default=SHImageWriter.default_colormap,
                        type=str)
    parser.add_argument('--version',
                        action='version',
                        version=pymchelper.__version__)
    args = parser.parse_args(args)

    # TODO add filename discovery

    files = sorted(glob.glob(args.inputfile))
    if not files:
        print('File does not exist: ' + args.inputfile)

    if args.outputfile is None:
        args.outputfile = files[0][:-3] + "txt"

    if args.many:
        merge_many(files, args.converter, args.nan, args.colormap)
    else:
        merge_list(files, args.outputfile, args.converter, args.nan,
                   args.colormap)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
