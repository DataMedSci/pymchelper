import os
import unittest

import tests.res.shieldhit.generated.generate_detect as gen


class TestGenerate(unittest.TestCase):
    def test_create(self):
        outfile = os.path.join("tests", "res", "shieldhit", "generated", "detect.dat")
        gen.main([outfile])
        self.assertTrue(os.path.isfile(outfile))


if __name__ == '__main__':
    unittest.main()
