import os
import unittest
import logging

import tests.res.fluka.generated.generate_input as gen

logger = logging.getLogger(__name__)


class TestFlukaGenerate(unittest.TestCase):
    def test_create(self):
        outdir = os.path.join("tests", "res", "fluka", "generated")
        gen.main([outdir])
        # for est in ("cyl", "geomap", "msh", "plane", "zone"):
        #     logger.info("Estimator: " + est)
        #     outfile = os.path.join(outdir, "detect_{:s}.dat".format(est))
        #     self.assertTrue(os.path.isfile(outfile))


if __name__ == '__main__':
    unittest.main()
