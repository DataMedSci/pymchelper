import sys
import unittest
import logging
import make_single_executable

logger = logging.getLogger(__name__)


class TestCallMain(unittest.TestCase):
    def test_run(self):
        logger.info("Preparing single executable")
        exit_code = make_single_executable.main()
        if sys.version_info > (3, 5):
            self.assertEqual(exit_code, 0)
        else:
            self.assertEqual(exit_code, 1)


if __name__ == '__main__':
    unittest.main()
