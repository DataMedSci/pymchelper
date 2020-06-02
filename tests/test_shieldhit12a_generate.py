import os
import tempfile
import unittest
import glob
import shutil
import logging

from pymchelper import run
from pymchelper.input_output import fromfile
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.shieldhit.particle import SHParticleType

import tests.res.shieldhit.generated.generate_detect as gen

logger = logging.getLogger(__name__)


class TestSHGenerate(unittest.TestCase):
    def test_create(self):
        outdir = os.path.join("tests", "res", "shieldhit", "generated")
        gen.main([outdir])
        for est in ("cyl", "geomap", "msh", "plane", "zone"):
            logger.info("Estimator: " + est)
            outfile = os.path.join(outdir, "detect_{:s}.dat".format(est))
            self.assertTrue(os.path.isfile(outfile))


class TestSHGenerated(unittest.TestCase):

    main_dir = os.path.join("tests", "res", "shieldhit", "generated")
    single_dir = os.path.join(main_dir, "single")
    many_dir = os.path.join(main_dir, "many")

    def test_many_plotdata(self):
        for est in ("cyl", "msh", "plane", "zone"):
            logger.info("Estimator: " + est)
            indir = os.path.join(self.many_dir, est)

            for add_options in ([], ["--error", "stderr"], ["--error", "stddev"], ["--error", "none"]):
                outdir = tempfile.mkdtemp()
                run_options = ["plotdata", "--many", '' + os.path.join(indir, "*.bdo") + '', outdir]
                run_options += add_options
                logger.info("Run options " + " ".join(run_options))
                run.main(run_options)
                files = os.listdir(outdir)
                dat_files = [f for f in files if f.endswith(".dat")]
                self.assertGreater(len(dat_files), 4)
                shutil.rmtree(outdir)

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
                run.main(["txt", infile, outfile])
                saved_file = outfile + ".txt"
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
                for options in ([], ["--error", "stderr"], ["--error", "stddev"], ["--error", "none"]):
                    logger.info("Option: " + " ".join(options))
                    fd, outfile = tempfile.mkstemp()
                    os.close(fd)
                    os.remove(outfile)
                    run.main(["plotdata", infile, outfile] + options)
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
                    for options in ([], ["--colormap", "gnuplot2"],
                                    ["--error", "stderr"], ["--error", "stddev"], ["--error", "none"]):
                        fd, outfile = tempfile.mkstemp()
                        os.close(fd)
                        os.remove(outfile)
                        run.main(["image", infile, outfile] + options)
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
                estimator = fromfile(infile)
                if estimator.geotyp == SHGeoType.zone:
                    self.assertIn(estimator.x.n, (1, 2, 3))
                    self.assertIn(estimator.y.n, (1, 2, 3))
                    self.assertIn(estimator.z.n, (1, 2, 3))
                else:
                    self.assertIn(estimator.x.n, (1, 10))
                    self.assertIn(estimator.y.n, (1, 10))
                    self.assertIn(estimator.z.n, (1, 10))
                self.assertEqual(estimator.geotyp, SHGeoType[est])
                self.assertNotEqual(estimator.pages[0].dettyp, SHDetType.none)
                self.assertIn(estimator.particle, (SHParticleType.all, SHParticleType.proton, SHParticleType.neutron))
                if estimator.geotyp == SHGeoType.geomap:
                    self.assertIn(estimator.pages[0].dettyp, (SHDetType.zone, SHDetType.medium, SHDetType.rho))
                elif estimator.geotyp == SHGeoType.plane:
                    self.assertIn(estimator.pages[0].dettyp, (SHDetType.counter, ))
                else:
                    self.assertIn(estimator.pages[0].dettyp,
                                  (SHDetType.energy, SHDetType.fluence, SHDetType.avg_energy, SHDetType.avg_beta))
                if estimator.pages[0].geotyp not in (SHGeoType.zone, SHGeoType.plane):
                    self.assertGreater(estimator.x.max_val, estimator.x.min_val)
                    self.assertGreater(estimator.y.max_val, estimator.y.min_val)
                    self.assertGreater(estimator.z.max_val, estimator.z.min_val)
                self.assertEqual(estimator.file_counter, 1)
                if estimator.geotyp == SHGeoType.geomap:
                    self.assertEqual(estimator.number_of_primaries, 1)
                else:
                    self.assertEqual(estimator.number_of_primaries, 1000)
                self.assertGreaterEqual(len(estimator.pages), 1)
                self.assertGreaterEqual(estimator.pages[0].data_raw.size, 1)


if __name__ == '__main__':
    unittest.main()
