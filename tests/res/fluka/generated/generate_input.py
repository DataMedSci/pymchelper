import os
import sys

import argparse
import logging

from tests.res.fluka.generated.generate_common import generate_fluka_file
from tests.res.fluka.generated.generate_common import set_geometry
from tests.res.fluka.generated.generate_usrbin import add_scoring_dimensions, add_scoring_filters

logger = logging.getLogger(__name__)


def generate_usrbin(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    generate_fluka_file(os.path.join(dirname, "dimensions.inp"), set_geometry, add_scoring_dimensions)
    generate_fluka_file(os.path.join(dirname, "filters.inp"), set_geometry, add_scoring_filters)


def generate_usrcoll(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    # TODO
    pass


def generate_usryield(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    # TODO
    pass


def generate_resnuclei(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    # TODO
    pass


def generate_usrtrack(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    # TODO
    pass


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument("outputdir", help='output directory', type=str)
    parsed_args = parser.parse_args(args)

    logger.info("outputdir " + parsed_args.outputdir)

    generate_usrbin(os.path.join(parsed_args.outputdir, "usrbin"))
    generate_usrcoll(os.path.join(parsed_args.outputdir, "usrcoll"))
    generate_usryield(os.path.join(parsed_args.outputdir, "usryield"))
    generate_resnuclei(os.path.join(parsed_args.outputdir, "resnuclei"))
    generate_usrtrack(os.path.join(parsed_args.outputdir, "usrtrack"))

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
