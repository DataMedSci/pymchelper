import os
import sys
from collections import OrderedDict

import argparse
import logging
from itertools import product

from pymchelper.flair.Input import Card
from pymchelper.shieldhit.detector.geometry import CarthesianMesh
from tests.res.fluka.generated.generate_common import generate_fluka_file
from tests.res.fluka.generated.generate_common import set_geometry

logger = logging.getLogger(__name__)


def add_scoring_dimensions(input_file):
    det_types = {"en": "ENERGY", "n": "NEUTRON"}

    nbins = 10
    xmin = -2.0
    xmax = -xmin
    ymin = xmin
    ymax = -ymin
    zmin = 0.0
    zmax = 30.0
    dx = 1.0
    dy = 1.0
    dz = 1.0

    mesh_types = OrderedDict()

    xmid = (xmin + xmax) / 2.0
    ymid = (ymin + ymax) / 2.0
    zmid = (zmin + zmax) / 2.0

    # 1-D
    geometry_x = CarthesianMesh()
    geometry_x.set_axis(axis_no=0, start=xmin, stop=xmax, nbins=nbins)
    geometry_x.set_axis(axis_no=1, start=ymid - dy, stop=ymid + dy, nbins=1)
    geometry_x.set_axis(axis_no=2, start=zmid - dz, stop=zmid + dz, nbins=1)
    mesh_types["x"] = geometry_x

    geometry_y = CarthesianMesh()
    geometry_y.set_axis(axis_no=0, start=xmid - dx, stop=xmid + dx, nbins=1)
    geometry_y.set_axis(axis_no=1, start=ymin, stop=ymax, nbins=nbins)
    geometry_y.set_axis(axis_no=2, start=zmid - dz, stop=zmid + dz, nbins=1)
    mesh_types["y"] = geometry_y

    geometry_z = CarthesianMesh()
    geometry_z.set_axis(axis_no=0, start=-dx, stop=xmid + dx, nbins=1)
    geometry_z.set_axis(axis_no=1, start=ymid - dy, stop=ymid + dy, nbins=1)
    geometry_z.set_axis(axis_no=2, start=zmin, stop=zmax, nbins=nbins)
    mesh_types["z"] = geometry_z

    # 2-D
    geometry_xy = CarthesianMesh()
    geometry_xy.set_axis(axis_no=0, start=xmin, stop=xmax, nbins=nbins)
    geometry_xy.set_axis(axis_no=1, start=ymin, stop=ymax, nbins=nbins)
    geometry_xy.set_axis(axis_no=2, start=zmid - dz, stop=zmid + dz, nbins=1)
    mesh_types["xy"] = geometry_xy

    geometry_yz = CarthesianMesh()
    geometry_yz.set_axis(axis_no=0, start=xmid - dx, stop=xmid + dx, nbins=1)
    geometry_yz.set_axis(axis_no=1, start=ymin, stop=ymax, nbins=nbins)
    geometry_yz.set_axis(axis_no=2, start=zmin, stop=zmax, nbins=nbins)
    mesh_types["yz"] = geometry_yz

    geometry_xz = CarthesianMesh()
    geometry_xz.set_axis(axis_no=0, start=xmin, stop=xmax, nbins=nbins)
    geometry_xz.set_axis(axis_no=1, start=ymid - dy, stop=ymid + dy, nbins=1)
    geometry_xz.set_axis(axis_no=2, start=zmin, stop=zmax, nbins=nbins)
    mesh_types["xz"] = geometry_xz

    # 3-D
    geometry_xyz = CarthesianMesh()
    geometry_xyz.set_axis(axis_no=0, start=xmin, stop=xmax, nbins=nbins)
    geometry_xyz.set_axis(axis_no=1, start=ymin, stop=ymax, nbins=nbins)
    geometry_xyz.set_axis(axis_no=2, start=zmin, stop=zmax, nbins=nbins)
    mesh_types["xyz"] = geometry_xyz

    # Fluka is using concept of output unit numbers, this is starting number,
    # for each new scorer will be decreased by one
    output_unit = -21

    # scoring, see http://www.fluka.org/fluka.php?id=man_onl&sub=84
    # template cards for USRBIN scorers:
    usrbin_card1 = Card("USRBIN")
    usrbin_card1.setWhat(1, 0.0)  # WHAT(1) - type of binning selected (0.0 : Mesh Cartesian, no sym.)
    usrbin_card2 = Card("USRBIN")
    usrbin_card2.setSdum("&")  # continuation card

    # loop over all possible detectors and meshes
    for det_type, mesh_type in product(det_types.keys(), mesh_types.keys()):

        # make copies of template cards
        card1 = usrbin_card1.clone()
        card2 = usrbin_card2.clone()

        # generate comment
        card1.setComment("scoring {:s} on mesh {:s}".format(det_types[det_type], mesh_type))
        card1.setSdum("{:s}_{:s}".format(det_type, mesh_type))  # SDUM - identifying the binning detector
        card1.setWhat(2, det_types[det_type])  # WHAT(2) - particle (or particle family) type to be scored
        card1.setWhat(3, output_unit)  # WHAT(3) - output unit (> 0.0 : formatted data,  < 0.0 : unformatted data)

        msh = mesh_types[mesh_type]
        card1.setWhat(4, msh.axis[0].stop)  # WHAT(4) - For Cartesian binning: Xmax
        card1.setWhat(5, msh.axis[1].stop)  # WHAT(5) - For Cartesian binning: Ymax
        card1.setWhat(6, msh.axis[2].stop)  # WHAT(6) - For Cartesian binning: Zmax
        card2.setWhat(1, msh.axis[0].start)  # WHAT(1) - For Cartesian binning: Xmin
        card2.setWhat(2, msh.axis[1].start)  # WHAT(2) - For Cartesian binning: Ymin
        card2.setWhat(3, msh.axis[2].start)  # WHAT(3) - For Cartesian binning: Zmin
        card2.setWhat(4, msh.axis[0].nbins)  # WHAT(4) - For Cartesian binning: number of X bins
        card2.setWhat(5, msh.axis[1].nbins)  # WHAT(5) - For Cartesian binning: number of Y bins
        card2.setWhat(6, msh.axis[2].nbins)  # WHAT(6) - For Cartesian binning: number of Z bins
        output_unit -= 1

        # finally add generated cards to input structure
        input_file.addCard(card1)
        card1.appendWhats(card2.whats()[1:])


def generate_usrbin(dirname):
    fname = "dimensions.inp"
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    generate_fluka_file(os.path.join(dirname, fname), set_geometry, add_scoring_dimensions)


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument("outputdir", help='output directory', type=str)
    parsed_args = parser.parse_args(args)

    logger.info("outputdir " + parsed_args.outputdir)

    generate_usrbin(os.path.join(parsed_args.outputdir, "usrbin"))

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
