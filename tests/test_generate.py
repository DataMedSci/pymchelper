import os
import unittest

import tests.res.shieldhit.generated.generate_detect as gen


class TestGenerate(unittest.TestCase):
    def test_create(self):
        outdir = os.path.join("tests", "res", "shieldhit", "generated")
        gen.main([outdir])
        outfile = os.path.join(outdir, "detect_geomap.dat")
        self.assertTrue(os.path.isfile(outfile))


if __name__ == '__main__':
    unittest.main()
