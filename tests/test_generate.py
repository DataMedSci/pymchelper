import os
import tempfile
import unittest
import glob
import logging

from pymchelper import run
from pymchelper.detector import Detector
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.shieldhit.particle import SHParticleType

import tests.res.shieldhit.generated.generate_detect as gen

logger = logging.getLogger(__name__)


class TestGenerate(unittest.TestCase):
    def test_create(self):
        outdir = os.path.join("tests", "res", "shieldhit", "generated")
        gen.main([outdir])
        for est in ("cyl", "geomap", "msh", "plane", "zone"):
            logger.info("Estimator: " + est)
            outfile = os.path.join(outdir, "detect_{:s}.dat".format(est))
            self.assertTrue(os.path.isfile(outfile))


class TestGenerated(unittest.TestCase):

    main_dir = os.path.join("tests", "res", "shieldhit", "generated")
    single_dir = os.path.join(main_dir, "single")
    many_dir = os.path.join(main_dir, "many")

    def test_many_image(self):
        for est in ("cyl", "msh", "plane", "zone"):
            logger.info("Estimator: " + est)
            outdir = os.path.join(self.many_dir, est)
            run.main(["--many", os.path.join(outdir, "*.bdo"), "--converter", "plotdata"])
            files = os.listdir(outdir)
            png_files = [f for f in files if f.endswith(".dat")]
            self.assertGreater(len(png_files), 4)

    def test_standard(self):
        for est in ("cyl", "geomap", "msh", "plane", "zone"):
            logger.info("Estimator: " + est)
            outdir = os.path.join(self.single_dir, est)
            bdo_files = glob.glob(os.path.join(outdir, "*.bdo"))
            self.assertGreater(len(bdo_files), 0)
            for infile in bdo_files:
                logger.info("Input file: " + infile)
                fd, outfile = tempfile.mkstemp()
                os.close(fd)
                os.remove(outfile)
                run.main([infile, outfile])
                saved_file = outfile
                self.assertTrue(os.path.isfile(saved_file))
                self.assertGreater(os.path.getsize(saved_file), 0)
                os.remove(saved_file)

    def test_plotdata(self):
        for est in ("cyl", "geomap", "msh", "plane", "zone"):
            logger.info("Estimator: " + est)
            outdir = os.path.join(self.single_dir, est)
            bdo_files = glob.glob(os.path.join(outdir, "*.bdo"))
            self.assertGreater(len(bdo_files), 0)
            for infile in bdo_files:
                logger.info("Input file: " + infile)
                fd, outfile = tempfile.mkstemp()
                os.close(fd)
                os.remove(outfile)
                run.main([infile, outfile, "--converter", "plotdata"])
                saved_file = outfile + ".dat"
                self.assertTrue(os.path.isfile(saved_file))
                self.assertGreater(os.path.getsize(saved_file), 0)
                os.remove(saved_file)

    def test_image(self):
        allowed_patterns = ("_x_", "_y_", "_z_", "_xy_", "_yz_", "_xz_")
        for est in ("cyl", "geomap", "msh", "plane", "zone"):
            logger.info("Estimator: " + est)
            outdir = os.path.join(self.single_dir, est)
            bdo_files = glob.glob(os.path.join(outdir, "*.bdo"))
            self.assertGreater(len(bdo_files), 0)
            for infile in bdo_files:
                logger.info("Input file: " + infile)
                will_produce_output = False
                for pattern in allowed_patterns:
                    if pattern in os.path.basename(infile):
                        will_produce_output = True
                if will_produce_output:
                    for options in ([], ["--colormap", "gnuplot2"]):
                        fd, outfile = tempfile.mkstemp()
                        os.close(fd)
                        os.remove(outfile)
                        run.main([infile, outfile, "--converter", "image"] + options)
                        saved_file = outfile + ".png"
                        self.assertTrue(os.path.isfile(saved_file))
                        self.assertGreater(os.path.getsize(saved_file), 0)
                        os.remove(saved_file)

    def test_get_object(self):
        for est in ("cyl", "geomap", "msh", "plane", "zone"):
            logger.info("Estimator: " + est)
            outdir = os.path.join(self.single_dir, est)
            bdo_files = glob.glob(os.path.join(outdir, "*.bdo"))
            self.assertGreater(len(bdo_files), 0)
            for infile in bdo_files:
                logger.info("Input file: " + infile)
                det = Detector()
                det.read(infile)
                if det.geotyp == SHGeoType.zone:
                    self.assertIn(det.nx, (1, 2, 3))
                    self.assertIn(det.ny, (1, 2, 3))
                    self.assertIn(det.nz, (1, 2, 3))
                else:
                    self.assertIn(det.nx, (1, 10))
                    self.assertIn(det.ny, (1, 10))
                    self.assertIn(det.nz, (1, 10))
                self.assertEqual(det.geotyp, SHGeoType[est])
                self.assertNotEqual(det.dettyp, SHDetType.unknown)
                self.assertIn(det.particle, (SHParticleType.all, SHParticleType.proton, SHParticleType.neutron))
                if det.geotyp == SHGeoType.geomap:
                    self.assertIn(det.dettyp, (SHDetType.zone, SHDetType.medium, SHDetType.rho))
                elif det.geotyp == SHGeoType.plane:
                    self.assertIn(det.dettyp, (SHDetType.counter, ))
                else:
                    self.assertIn(det.dettyp,
                                  (SHDetType.energy, SHDetType.fluence, SHDetType.avg_energy, SHDetType.avg_beta))
                if det.geotyp not in (SHGeoType.zone, SHGeoType.plane):
                    self.assertGreater(det.xmax, det.xmin)
                    self.assertGreater(det.ymax, det.ymin)
                    self.assertGreater(det.zmax, det.zmin)
                self.assertEqual(det.counter, 1)
                if det.geotyp == SHGeoType.geomap:
                    self.assertEqual(det.nstat, 1)
                else:
                    self.assertEqual(det.nstat, 1000)
                self.assertGreaterEqual(len(det.data), 1)


if __name__ == '__main__':
    unittest.main()
