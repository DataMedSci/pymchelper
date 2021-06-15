import numpy as np

from pymchelper.axis import MeshAxis, AxisId


class Page:
    def __init__(self, estimator=None):

        self.estimator = estimator

        self.data_raw = np.array([float("NaN")])  # linear data storage
        self.error_raw = np.array([float("NaN")])  # linear data storage

        self.name = ""
        self.unit = ""

        self.dettyp = None  # Dose, Fluence, LET etc...

        # optional first differential axis
        self.diff_axis1 = MeshAxis(n=1,
                                   min_val=float("NaN"),
                                   max_val=float("NaN"),
                                   name="",
                                   unit="",
                                   binning=MeshAxis.BinningType.linear)

        # optional second differential axis
        self.diff_axis2 = MeshAxis(n=1,
                                   min_val=float("NaN"),
                                   max_val=float("NaN"),
                                   name="",
                                   unit="",
                                   binning=MeshAxis.BinningType.linear)

    def axis(self, axis_id):
        """
        TODO
        """
        if axis_id == AxisId.diff1:
            return self.diff_axis1
        elif axis_id == AxisId.diff2:
            return self.diff_axis2
        elif self.estimator:
            return self.estimator.axis(axis_id)
        return None

    @property
    def dimension(self):
        """
        Let's take again detector d with YZ scoring.
        >>> from pymchelper.estimator import Estimator
        >>> e = Estimator()
        >>> e.x = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.z = MeshAxis(n=2, min_val=0.0, max_val=2.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.dimension
        2
        >>> p = Page(e)
        >>> p.diff_axis1 = MeshAxis(n=10, min_val=0.0, max_val=100.0, name="E", unit="MeV",
        ...                         binning=MeshAxis.BinningType.linear)
        >>> p.dimension
        3

        :return: number of page axes (including differential) which have more than one bin
        """
        if self.estimator:
            return 2 - (self.diff_axis1.n, self.diff_axis2.n).count(1) + self.estimator.dimension
        else:
            return None

    @property
    def data(self):
        """
        3-D view of page data.

        Page data is stored originally in `data_raw` 1-D array.
        This property provides efficient view of data, suitable for numpy-like indexing.

        >>> from pymchelper.estimator import Estimator
        >>> e = Estimator()
        >>> e.x = MeshAxis(n=2, min_val=0.0, max_val=10.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.z = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> p = Page(estimator=e)
        >>> p.data_raw = np.arange(6)
        >>> tuple(int(n) for n in p.data.shape)
        (2, 3, 1, 1, 1)
        >>> p.data[1, 2, 0, 0, 0]
        5

        :return: reshaped view of ``data_raw``
        """
        if self.estimator:
            return self._reshape(data_1d=self.data_raw,
                                 shape=(self.estimator.x.n, self.estimator.y.n, self.estimator.z.n,
                                        self.diff_axis1.n, self.diff_axis2.n))
        return None

    @property
    def error(self):
        """
        3-D view of page error

        For more details see ``data`` property.
        :return:
        """
        if self.estimator:
            return self._reshape(data_1d=self.error_raw,
                                 shape=(self.estimator.x.n, self.estimator.y.n, self.estimator.z.n,
                                        self.diff_axis1.n, self.diff_axis2.n))
        return None

    def _reshape(self, data_1d, shape):
        # TODO check also  tests/res/shieldhit/single/ex_yzmsh.bdo as it is saved in bin2010 format
        if self.estimator:
            order = 'C'
            if self.estimator.file_format in ('bdo2016', 'bdo2019', 'fluka_binary'):
                order = 'F'
            return data_1d.reshape(shape, order=order)
        else:
            return None

    def plot_axis(self, id):
        """
        Calculate new order of detector axis, axis with data (n>1) comes first
        Axes with constant value goes last.

        Let's take a detector d with YZ scoring.
        >>> from pymchelper.estimator import Estimator
        >>> e = Estimator()
        >>> e.x = MeshAxis(n=1, min_val=0.0, max_val=1.0, name="X", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.y = MeshAxis(n=3, min_val=0.0, max_val=150.0, name="Y", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> e.z = MeshAxis(n=2, min_val=0.0, max_val=2.0, name="Z", unit="cm", binning=MeshAxis.BinningType.linear)
        >>> p = Page(estimator=e)
        >>> e.add_page(page=p)

        First axis for plotting will be Y (as X axis holds only one bin):
        >>> p.plot_axis(0)
        MeshAxis(n=3, min_val=0.0, max_val=150.0, name='Y', unit='cm', binning=<BinningType.linear: 0>)

        Second axis for plotting will be Z (its the next after Y with n > 1 bins)
        >>> p.plot_axis(1)
        MeshAxis(n=2, min_val=0.0, max_val=2.0, name='Z', unit='cm', binning=<BinningType.linear: 0>)

        Finally the third axis will be X, but it cannot be used for plotting as it has only one bin.
        >>> p.plot_axis(2)
        MeshAxis(n=1, min_val=0.0, max_val=1.0, name='X', unit='cm', binning=<BinningType.linear: 0>)


        :param id: axis number (0, 1, 2, 3 or 4)
        :return: axis object
        """
        plotting_order = (AxisId.x, AxisId.y, AxisId.z, AxisId.diff1, AxisId.diff2)
        variable_axes_id = [i for i in plotting_order if self.axis(i).n > 1]
        constant_axes_id = [i for i in plotting_order if self.axis(i).n == 1]
        plotting_order = variable_axes_id + constant_axes_id
        return self.axis(plotting_order[id])
