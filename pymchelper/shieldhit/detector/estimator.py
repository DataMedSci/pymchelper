import logging

from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.shieldhit.detector.geometry import Geometry
from pymchelper.shieldhit.particle import SHParticleType, SHHeavyIonType

logger = logging.getLogger(__name__)


class SHEstimator:
    allowed_detectors = {
        SHGeoType.unknown: (),
        SHGeoType.zone: (SHDetType(i + 1) for i in range(SHDetType.tletg - 1)),
        SHGeoType.cyl: (SHDetType(i + 1) for i in range(SHDetType.tletg - 1)),
        SHGeoType.msh: (SHDetType(i + 1) for i in range(SHDetType.tletg - 1)),
        SHGeoType.plane: (SHDetType(i + 1) for i in range(SHDetType.tletg - 1)),
        SHGeoType.dzone: (SHDetType(i + 1) for i in range(SHDetType.tletg - 1)),
        SHGeoType.dcyl: (SHDetType(i + 1) for i in range(SHDetType.tletg - 1)),
        SHGeoType.dmsh: (SHDetType(i + 1) for i in range(SHDetType.tletg - 1)),
        SHGeoType.dplane: (SHDetType(i + 1) for i in range(SHDetType.tletg - 1)),
        SHGeoType.dcylz: (SHDetType(i + 1) for i in range(SHDetType.tletg - 1)),
        SHGeoType.dmshz: (SHDetType(i + 1) for i in range(SHDetType.tletg - 1)),
        SHGeoType.trace: (SHDetType.unknown, ),
        SHGeoType.voxscore: (SHDetType(i + 1) for i in range(SHDetType.tletg - 1)),
        SHGeoType.geomap: (SHDetType.zone, SHDetType.medium, SHDetType.rho),
    }

    def __init__(self):
        self.estimator = SHGeoType.unknown
        self.particle_type = SHParticleType.unknown
        self.heavy_ion_type = SHHeavyIonType()
        self.detector_type = SHDetType.unknown
        self.geometry = Geometry()
        self.filename = ""

    def is_valid(self):
        if self.estimator not in self.geometry.allowed_estimators():
            logger.error("{:s} is not a valid estimator for {:s} " "geometry".format(self.estimator, self.geometry))
            return False

        return True
