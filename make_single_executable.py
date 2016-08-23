#!/usr/bin/env python
import logging
import sys

logging.basicConfig()
logger = logging.getLogger(__name__)


def main(args=sys.argv[1:]):
    try:
        import zipapp
    except ImportError:
        logger.error("zippapp module not available, use Python version > 3.5. "
                     "Current python version:\n {:s}".format(sys.version))
        return 1
    zipapp.create_archive(
        source='.', target='convertmc.pyz', main='pymchelper.run:main', interpreter="/usr/bin/env python")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
