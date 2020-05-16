import logging

from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.shieldhit.detector.geometry import Geometry
from pymchelper.shieldhit.particle import SHParticleType, SHHeavyIonType

logger = logging.getLogger(__name__)


class SHEstimator:
    # (internal) Number of detector to be used with most scorers.
    # This correspons to the last "normal" detector minus 1, since the 0 detector is not inlucded.
    # Update the last detector if new detectors are added.
    _nn_det = SHDetType.flu_neqv - 1

    allowed_detectors = {
        SHGeoType.unknown: (),
        SHGeoType.zone: (SHDetType(i + 1) for i in range(_nn_det)),
        SHGeoType.cyl: (SHDetType(i + 1) for i in range(_nn_det)),
        SHGeoType.msh: (SHDetType(i + 1) for i in range(_nn_det)),
        SHGeoType.plane: (SHDetType(i + 1) for i in range(_nn_det)),
        SHGeoType.dzone: (SHDetType(i + 1) for i in range(_nn_det)),
        SHGeoType.dcyl: (SHDetType(i + 1) for i in range(_nn_det)),
        SHGeoType.dmsh: (SHDetType(i + 1) for i in range(_nn_det)),
        SHGeoType.dplane: (SHDetType(i + 1) for i in range(_nn_det)),
        SHGeoType.dcylz: (SHDetType(i + 1) for i in range(_nn_det)),
        SHGeoType.dmshz: (SHDetType(i + 1) for i in range(_nn_det)),
        SHGeoType.trace: (SHDetType.none,),
        SHGeoType.voxscore: (SHDetType(i + 1) for i in range(_nn_det)),
        SHGeoType.geomap: (SHDetType.zone, SHDetType.medium, SHDetType.rho),
    }

    def __init__(self):
        self.estimator = SHGeoType.unknown
        self.particle_type = SHParticleType.unknown
        self.heavy_ion_type = SHHeavyIonType()
        self.detector_type = SHDetType.none
        self.geometry = Geometry()
        self.filename = ""

    def is_valid(self):
        if self.estimator not in self.geometry.allowed_estimators():
            logger.error("{:s} is not a valid estimator for {:s} " "geometry".format(self.estimator, self.geometry))
            return False

        return True
