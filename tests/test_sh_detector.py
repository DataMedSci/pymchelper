import unittest

import pytest

from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator import SHGeoType, SHEstimator
from pymchelper.shieldhit.detector.fortran_card import CardLine, EstimatorWriter
from pymchelper.shieldhit.detector.geometry import CarthesianMesh, CylindricalMesh, Zone, Plane
from pymchelper.shieldhit.particle import SHParticleType, SHHeavyIonType


@pytest.mark.smoke
class TestSHDetector(unittest.TestCase):

    def test_create(self):
        d0 = SHDetType(0)
        self.assertEqual(d0, SHDetType.none)
        self.assertEqual(str(d0), "NONE")

        d1 = SHDetType(1)
        self.assertEqual(d1, SHDetType.energy)
        self.assertEqual(str(d1), "ENERGY")

        try:
            d1 = SHDetType(-1)
        except Exception as e:
            self.assertIsInstance(e, ValueError)


@pytest.mark.smoke
class TestSHParticle(unittest.TestCase):

    def test_create(self):
        p_all = SHParticleType(-1)
        self.assertEqual(p_all, SHParticleType.all)
        self.assertEqual(str(p_all), "all")

        p_proton = SHParticleType(2)
        self.assertEqual(p_proton, SHParticleType.proton)
        self.assertEqual(str(p_proton), "proton")

        p_carbon_ion = SHHeavyIonType()
        p_carbon_ion.z = 6
        p_carbon_ion.a = 12
        self.assertEqual(p_carbon_ion.particle_type, SHParticleType.heavy_ion)
        self.assertEqual(str(p_carbon_ion), "heavy-ion_6^12")

        try:
            SHParticleType(-2)
        except Exception as e:
            self.assertIsInstance(e, ValueError)


@pytest.mark.smoke
class TestFortranCard(unittest.TestCase):

    def test_create_string(self):
        comment = CardLine.comment
        self.assertEqual(len(comment), CardLine.no_of_elements * CardLine.element_length)

        self.assertEqual(CardLine.any_to_element(""), " " * CardLine.element_length)

        self.assertEqual(CardLine.any_to_element("  "), " " * CardLine.element_length)

        self.assertEqual(CardLine.any_to_element(" abc"), "       abc")

        self.assertEqual(CardLine.any_to_element("0123456789"), "0123456789")

        try:
            CardLine.any_to_element("0123456789a")
        except Exception as e:
            self.assertIsInstance(e, Exception)

    def test_create_number(self):
        self.assertEqual(CardLine.any_to_element(""), " " * CardLine.element_length)

        self.assertEqual(CardLine.any_to_element(0), "         0")

        self.assertEqual(CardLine.any_to_element(123), "       123")

        self.assertEqual(CardLine.any_to_element(-123), "      -123")

        self.assertEqual(CardLine.any_to_element(0.0), "       0.0")

        self.assertEqual(CardLine.any_to_element(1.), "       1.0")

        self.assertEqual(CardLine.any_to_element(-2.), "      -2.0")

        self.assertEqual(CardLine.any_to_element(-1. / 2.0), "      -0.5")

        self.assertEqual(CardLine.any_to_element(1234567890), "1234567890")

        try:
            CardLine.any_to_element(12345678900)
        except Exception as e:
            self.assertIsInstance(e, Exception)


@pytest.mark.smoke
class TestEstimatorWriter(unittest.TestCase):

    def test_write_msh(self):
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
        estimator.detector_type = SHDetType.energy
        estimator.particle_type = SHParticleType.all
        estimator.filename = "ex_zmsh"
        line1, line2 = EstimatorWriter.get_lines(estimator)
        ref_line1 = "MSH             -5.0      -5.0       0.0       5.0       5.0      30.0"
        ref_line2 = "                   1         1       300        -1    ENERGY   ex_zmsh"
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)

    def test_write_cyl(self):
        estimator = SHEstimator()
        estimator.estimator = SHGeoType.cyl
        estimator.geometry = CylindricalMesh()
        estimator.geometry.axis[0].start = 0.0
        estimator.geometry.axis[1].start = 0.0
        estimator.geometry.axis[2].start = 0.0
        estimator.geometry.axis[0].stop = 10.0
        estimator.geometry.axis[1].stop = 7.0
        estimator.geometry.axis[2].stop = 30.0
        estimator.geometry.axis[0].nbins = 1
        estimator.geometry.axis[1].nbins = 1
        estimator.geometry.axis[2].nbins = 300
        estimator.detector_type = SHDetType.energy
        estimator.particle_type = SHParticleType.all
        estimator.filename = "ex_cyl"
        line1, line2 = EstimatorWriter.get_lines(estimator)
        ref_line1 = "CYL              0.0       0.0       0.0      10.0       7.0      30.0"
        ref_line2 = "                   1         1       300        -1    ENERGY    ex_cyl"
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)

        estimator.detector_type = SHDetType.avg_beta
        estimator.particle_type = SHParticleType.proton
        ref_line2 = "                   1         1       300         2  AVG-BETA    ex_cyl"
        line1, line2 = EstimatorWriter.get_lines(estimator)
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)

        estimator.particle_type = SHParticleType.heavy_ion
        estimator.heavy_ion_type.a = 12
        estimator.heavy_ion_type.z = 6
        ref_line2 = "                   1         1       300        25  AVG-BETA    ex_cyl"
        ref_line3 = "                   6        12                                        "
        line1, line2, line3 = EstimatorWriter.get_lines(estimator)
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)
        self.assertEqual(str(line3), ref_line3)

    def test_write_cyl_compact(self):
        estimator = SHEstimator()
        estimator.estimator = SHGeoType.cyl
        estimator.geometry = CylindricalMesh()
        estimator.geometry.set_axis(axis_no=0, start=0.0, stop=10.0, nbins=1)
        estimator.geometry.set_axis(axis_no=1, start=0.0, stop=7.0, nbins=1)
        estimator.geometry.set_axis(axis_no=2, start=0.0, stop=30.0, nbins=300)
        estimator.detector_type = SHDetType.energy
        estimator.particle_type = SHParticleType.all
        estimator.filename = "ex_cyl"
        line1, line2 = EstimatorWriter.get_lines(estimator)
        ref_line1 = "CYL              0.0       0.0       0.0      10.0       7.0      30.0"
        ref_line2 = "                   1         1       300        -1    ENERGY    ex_cyl"
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)

    def test_write_geomap(self):
        estimator = SHEstimator()
        estimator.estimator = SHGeoType.geomap
        estimator.geometry = CarthesianMesh()
        estimator.geometry.axis[0].start = -1.0
        estimator.geometry.axis[1].start = -25.0
        estimator.geometry.axis[2].start = -15.0
        estimator.geometry.axis[0].stop = 1.0
        estimator.geometry.axis[1].stop = 25.0
        estimator.geometry.axis[2].stop = 35.0
        estimator.geometry.axis[0].nbins = 1
        estimator.geometry.axis[1].nbins = 50
        estimator.geometry.axis[2].nbins = 50
        estimator.detector_type = SHDetType.zone
        estimator.particle_type = SHParticleType.unknown
        estimator.filename = "ex_yzzon"
        line1, line2 = EstimatorWriter.get_lines(estimator)
        ref_line1 = "GEOMAP          -1.0     -25.0     -15.0       1.0      25.0      35.0"
        ref_line2 = "                   1        50        50         0      ZONE  ex_yzzon"
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)

        estimator.detector_type = SHDetType.medium
        line1, line2 = EstimatorWriter.get_lines(estimator)
        ref_line2 = "                   1        50        50         0    MEDIUM  ex_yzzon"
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)

        estimator.detector_type = SHDetType.rho
        line1, line2 = EstimatorWriter.get_lines(estimator)
        ref_line2 = "                   1        50        50         0       RHO  ex_yzzon"
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)

    def test_write_geomap_compact(self):
        estimator = SHEstimator()
        estimator.estimator = SHGeoType.geomap
        estimator.geometry = CarthesianMesh()
        estimator.geometry.set_axis(axis_no=0, start=-1.0, stop=1.0, nbins=1)
        estimator.geometry.set_axis(axis_no=1, start=-25.0, stop=25.0, nbins=50)
        estimator.geometry.set_axis(axis_no=2, start=-15.0, stop=35.0, nbins=50)
        estimator.detector_type = SHDetType.zone
        estimator.particle_type = SHParticleType.unknown
        estimator.filename = "ex_yzzon"
        line1, line2 = EstimatorWriter.get_lines(estimator)
        ref_line1 = "GEOMAP          -1.0     -25.0     -15.0       1.0      25.0      35.0"
        ref_line2 = "                   1        50        50         0      ZONE  ex_yzzon"
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)

    def test_write_zone(self):
        estimator = SHEstimator()
        estimator.estimator = SHGeoType.zone
        estimator.geometry = Zone()
        estimator.geometry.start = 1
        estimator.detector_type = SHDetType.dose
        estimator.particle_type = SHParticleType.all
        estimator.filename = "DH_dose"
        line1, = EstimatorWriter.get_lines(estimator)
        ref_line1 = "ZONE               1                            -1      DOSE   DH_dose"
        self.assertEqual(str(line1), ref_line1)

        estimator.geometry.stop = 300
        line1, = EstimatorWriter.get_lines(estimator)
        ref_line1 = "ZONE               1       300                  -1      DOSE   DH_dose"
        self.assertEqual(str(line1), ref_line1)

        estimator.particle_type = SHParticleType.heavy_ion
        estimator.heavy_ion_type.a = 12
        estimator.heavy_ion_type.z = 6
        line1, line2 = EstimatorWriter.get_lines(estimator)
        ref_line1 = "ZONE               1       300                  25      DOSE   DH_dose"
        ref_line2 = "                   6        12                                        "
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)

    def test_write_plane(self):
        estimator = SHEstimator()
        estimator.estimator = SHGeoType.plane
        estimator.geometry = Plane()
        estimator.geometry.point_x = 0.0
        estimator.geometry.point_y = 0.0
        estimator.geometry.point_z = 0.0
        estimator.geometry.normal_x = 0.0
        estimator.geometry.normal_y = 0.0
        estimator.geometry.normal_z = 1.0
        estimator.detector_type = SHDetType.counter
        estimator.particle_type = SHParticleType.all
        estimator.filename = "NB_count1"
        line1, line2 = EstimatorWriter.get_lines(estimator)
        ref_line1 = "PLANE            0.0       0.0       0.0       0.0       0.0       1.0"
        ref_line2 = "                                                -1   COUNTER NB_count1"
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)

    def test_write_plane_compact(self):
        estimator = SHEstimator()
        estimator.estimator = SHGeoType.plane
        estimator.geometry = Plane()
        estimator.geometry.set_point(x=0.0, y=0.0, z=0.0)
        estimator.geometry.set_normal(x=0.0, y=0.0, z=1.0)
        estimator.detector_type = SHDetType.counter
        estimator.particle_type = SHParticleType.proton
        estimator.filename = "NB_count2"
        line1, line2 = EstimatorWriter.get_lines(estimator)
        ref_line1 = "PLANE            0.0       0.0       0.0       0.0       0.0       1.0"
        ref_line2 = "                                                 2   COUNTER NB_count2"
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)


if __name__ == '__main__':
    unittest.main()
