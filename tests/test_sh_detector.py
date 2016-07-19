import unittest
from pymchelper.shieldhit.detector.detector import SHDetType


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

if __name__ == '__main__':
    unittest.main()
