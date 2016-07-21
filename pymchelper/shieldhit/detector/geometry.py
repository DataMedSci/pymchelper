from pymchelper.shieldhit.detector.estimator_type import SHGeoType


class Axis:
    def __init__(self, name="", start=None, stop=None, nbins=None):
        self.name = name
        self.set(start=start, stop=stop, nbins=nbins)

    def set(self, start=None, stop=None, nbins=None):
        self.start = start
        self.stop = stop
        self.nbins = nbins


class Geometry:
    def __init__(self):
        self.axis = (Axis(), Axis(), Axis())

    @staticmethod
    def allowed_estimators():
        return ()

    def set_axis(self, axis_no, start=None, stop=None, nbins=None):
        self.axis[axis_no].set(start=start, stop=stop, nbins=nbins)

    def __str__(self):
        return "general"


class CarthesianMesh(Geometry):
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
    def __init__(self):
        self.start = None
        self.stop = None

    @staticmethod
    def allowed_estimators():
        return SHGeoType.zone, SHGeoType.dzone

    def __str__(self):
        return "zone"


class Plane:
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
