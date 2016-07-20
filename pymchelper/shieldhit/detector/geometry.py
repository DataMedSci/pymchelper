from pymchelper.shieldhit.detector.estimator_type import SHGeoType


class Axis:
    def __init__(self):
        self.name = ""
        self.start = None
        self.stop = None
        self.nbins = None


class Geometry:
    def __init__(self):
        self.axis = (Axis(), Axis(), Axis())

    @staticmethod
    def allowed_estimators():
        return ()

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
