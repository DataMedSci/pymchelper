import unittest
from pymchelper.shieldhit.detector.detector import SHDetType
from pymchelper.shieldhit.detector.estimator import SHGeoType, SHEstimator
from pymchelper.shieldhit.detector.fortran_card import CardLine, \
    EstimatorWriter
from pymchelper.shieldhit.detector.geometry import CarthesianMesh
from pymchelper.shieldhit.particle import SHParticleType, SHHeavyIonType


class TestSHDetector(unittest.TestCase):
    def test_create(self):
        d0 = SHDetType(0)
        self.assertEqual(d0, SHDetType.unknown)
        self.assertEqual(str(d0), "UNKNOWN")

        d1 = SHDetType(1)
        self.assertEqual(d1, SHDetType.energy)
        self.assertEqual(str(d1), "ENERGY")

        try:
            d1 = SHDetType(-1)
        except Exception as e:
            self.assertIsInstance(e, ValueError)


class TestSHParticle(unittest.TestCase):
    def test_create(self):
        p_all = SHParticleType(-1)
        self.assertEqual(p_all, SHParticleType.all)
        self.assertEqual(str(p_all), "all")

        p_proton = SHParticleType(2)
        self.assertEqual(p_proton, SHParticleType.proton)
        self.assertEqual(str(p_proton), "proton")

        p_carbon_ion = SHHeavyIonType(6, 12)
        self.assertEqual(p_carbon_ion.particle_type, SHParticleType.heavy_ion)
        self.assertEqual(str(p_carbon_ion), "heavy-ion_6^12")

        try:
            SHParticleType(-2)
        except Exception as e:
            self.assertIsInstance(e, ValueError)


class TestFortranCard(unittest.TestCase):
    def test_create_string(self):
        comment = CardLine.comment
        self.assertEqual(len(comment),
                         CardLine.no_of_elements * CardLine.element_length)

        self.assertEqual(CardLine.string_to_element(""),
                         " " * CardLine.element_length)

        self.assertEqual(CardLine.string_to_element("  "),
                         " " * CardLine.element_length)

        self.assertEqual(CardLine.string_to_element(" abc"),
                         "       abc")

        self.assertEqual(CardLine.string_to_element("0123456789"),
                         "0123456789")

        try:
            CardLine.string_to_element("0123456789a")
        except Exception as e:
            self.assertIsInstance(e, Exception)

    def test_create_number(self):
        self.assertEqual(CardLine.number_to_element(""),
                         " " * CardLine.element_length)

        self.assertEqual(CardLine.number_to_element(0),
                         "         0")

        self.assertEqual(CardLine.number_to_element(123),
                         "       123")

        self.assertEqual(CardLine.number_to_element(-123),
                         "      -123")

        self.assertEqual(CardLine.number_to_element(0.0),
                         "       0.0")

        self.assertEqual(CardLine.number_to_element(1.),
                         "       1.0")

        self.assertEqual(CardLine.number_to_element(-2.),
                         "      -2.0")

        self.assertEqual(CardLine.number_to_element(-1. / 2.0),
                         "      -0.5")

        self.assertEqual(CardLine.number_to_element(1234567890),
                         "1234567890")

        try:
            CardLine.number_to_element(12345678900)
        except Exception as e:
            self.assertIsInstance(e, Exception)


class TestEstimatorWriter(unittest.TestCase):
    def test_write(self):
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
        line1, line2 = EstimatorWriter.write(estimator)
        ref_line1 = "       MSH      -5.0      -5.0       0.0" \
                    "       5.0       5.0      30.0"
        ref_line2 = "                   1         1       300" \
                    "        -1    ENERGY   ex_zmsh"
        self.assertEqual(str(line1), ref_line1)
        self.assertEqual(str(line2), ref_line2)

if __name__ == '__main__':
    unittest.main()
