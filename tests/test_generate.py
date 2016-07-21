import os
import unittest

import tests.res.shieldhit.generated.generate_detect as gen


class TestGenerate(unittest.TestCase):
    def test_create(self):
        outdir = os.path.join("tests", "res", "shieldhit", "generated")
        gen.main([outdir])
        for est in ("cyl", "geomap", "msh", "plane", "zone"):
            outfile = os.path.join(outdir, "detect_{:s}.dat".format(est))
            self.assertTrue(os.path.isfile(outfile))


class TestGenerated(unittest.TestCase):
    def test_geomap(self):
        pass
#        outdir = os.path.join("tests", "res", "shieldhit", "generated")


if __name__ == '__main__':
    unittest.main()
