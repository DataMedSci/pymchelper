import sys

from pymchelper.shieldhit.detector.detector import SHDetType
from pymchelper.shieldhit.detector.estimator import SHEstimator
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.shieldhit.detector.fortran_card import EstimatorWriter, CardLine
from pymchelper.shieldhit.detector.geometry import CarthesianMesh
from pymchelper.shieldhit.particle import SHParticleType


def main(args=sys.argv[1:]):
    estimator = SHEstimator()
    estimator.estimator = SHGeoType.msh
    estimator.geometry = CarthesianMesh()
    estimator.geometry.axis[0].start = -5.0
    estimator.geometry.axis[1].start = -5.0
    estimator.geometry.axis[2].start = 0.0
    estimator.geometry.axis[0].stop = 5.0
    estimator.geometry.axis[1].stop = 5.0
    estimator.geometry.axis[2].stop = 30.0
    estimator.geometry.axis[0].nbins = 1
    estimator.geometry.axis[1].nbins = 1
    estimator.geometry.axis[2].nbins = 300
    line1, line2 = EstimatorWriter.write(estimator)
    config = [(SHDetType.energy, SHParticleType.proton, "ex_en_pr"),
              (SHDetType.energy, SHParticleType.neutron, "ex_en_ne"),
              (SHDetType.energy, SHParticleType.all, "ex_en_all"), (SHDetType.let, SHParticleType.all, "ex_let_all")]
    with open("detect.dat", "w") as f:
        for det_type, particle, filename in config:
            estimator.detector_type = det_type
            estimator.particle_type = particle
            estimator.filename = filename
            line1, line2 = EstimatorWriter.write(estimator)
            f.write(CardLine.comment + "\n")
            f.write(str(line1) + "\n")
            f.write(str(line2) + "\n")
        f.write(CardLine.comment + "\n")


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
