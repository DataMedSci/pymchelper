from pymchelper.shieldhit.detector.estimator_type import SHGeoType


class Axis:
    """
    Represents named sequence of nbins numbers, with known start and end position.
    Can be used as container to describe scoring geometry along one of the axis.
    """

    def __init__(self, name="", start=None, stop=None, nbins=None):
        self.name = name
        self.set(start=start, stop=stop, nbins=nbins)

    def set(self, start=None, stop=None, nbins=None):
        self.start = start
        self.stop = stop
        self.nbins = nbins


class Geometry:
    """
    Base class for all types of scoring geometries. Holds information about three axes.
    Three axis are used to allow scoring up to 3 dimensions.
    Lower number of dimensions (i.e. scoring on square) are achieved by setting nbins=1 in the axis.
    """

    def __init__(self):
        self.axis = (Axis(), Axis(), Axis())

    @staticmethod
    def allowed_estimators():
        """
        :return: List of compatible estimators for this scoring geometry.
        """
        return ()

    def set_axis(self, axis_no, start=None, stop=None, nbins=None):
        """
        Fill axis data
        :param axis_no: integer number, from 0 to 2, specifies axis number
        :param start: start position
        :param stop:  stop position
        :param nbins: number of elements
        :return: None
        """
        if axis_no in range(len(self.axis)):
            self.axis[axis_no].set(start=start, stop=stop, nbins=nbins)

    def __str__(self):
        return "general"


class CarthesianMesh(Geometry):
    """
    Carthesian mesh along X,Y and Z axis
    """

    def __init__(self):
        Geometry.__init__(self)
        self.axis[0].name = "X"
        self.axis[1].name = "Y"
        self.axis[2].name = "Z"

    @staticmethod
    def allowed_estimators():
        return SHGeoType.msh, SHGeoType.dmsh, SHGeoType.geomap

    def __str__(self):
        return "carthesian"


class CylindricalMesh(Geometry):
    """
    Cylindrical mesh along R, PHI and Z axis
    """

    def __init__(self):
        Geometry.__init__(self)
        self.axis[0].name = "R"
        self.axis[1].name = "PHI"
        self.axis[2].name = "Z"

    @staticmethod
    def allowed_estimators():
        return SHGeoType.cyl, SHGeoType.dcyl

    def __str__(self):
        return "cylindrical"


class Zone:
    """
    Zone scoring geometry - start and stop
    """

    def __init__(self):
        self.start = None
        self.stop = None

    @staticmethod
    def allowed_estimators():
        return SHGeoType.zone, SHGeoType.dzone

    def __str__(self):
        return "zone"


class Plane:
    """
    Plane scoring geometry
    """

    def __init__(self):
        self.set_point()
        self.set_normal()

    def set_point(self, x=None, y=None, z=None):
        self.point_x = x
        self.point_y = y
        self.point_z = z

    def set_normal(self, x=None, y=None, z=None):
        self.normal_x = x
        self.normal_y = y
        self.normal_z = z

    @staticmethod
    def allowed_estimators():
        return SHGeoType.plane, SHGeoType.dplane

    def __str__(self):
        return "plane"
