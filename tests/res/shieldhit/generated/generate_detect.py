import argparse
import sys
from itertools import product

# import necessary code pieces from pymchelper
from pymchelper.shieldhit.detector.detector import SHDetType
from pymchelper.shieldhit.detector.estimator import SHEstimator
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.shieldhit.detector.fortran_card import EstimatorWriter, CardLine
from pymchelper.shieldhit.detector.geometry import CarthesianMesh
from pymchelper.shieldhit.particle import SHParticleType


def geomap_geometries():
    nbins = 10
    xmin = -20.0
    xmax = -xmin
    ymin = xmin
    ymax = -ymin
    zmin = -10.0
    zmax = 30.0
    dx = 1.0
    dy = 1.0
    dz = 1.0

    result = {}

    # 0-D
    geometry = CarthesianMesh()
    geometry.set_axis(axis_no=0, start=-dx, stop=dx, nbins=1)
    geometry.set_axis(axis_no=1, start=-dy, stop=dy, nbins=1)
    geometry.set_axis(axis_no=2, start=5.0, stop=6.0, nbins=1)
    result["0"] = geometry

    # 1-D
    geometry_x = CarthesianMesh()
    geometry_x.set_axis(axis_no=0, start=xmin, stop=xmax, nbins=nbins)
    geometry_x.set_axis(axis_no=1, start=-dy, stop=dy, nbins=1)
    geometry_x.set_axis(axis_no=2, start=-dz, stop=dz, nbins=1)
    result["x"] = geometry_x

    geometry_y = CarthesianMesh()
    geometry_y.set_axis(axis_no=0, start=-dx, stop=dx, nbins=1)
    geometry_y.set_axis(axis_no=1, start=ymin, stop=ymax, nbins=nbins)
    geometry_y.set_axis(axis_no=2, start=-dz, stop=dz, nbins=1)
    result["y"] = geometry_y

    geometry_z = CarthesianMesh()
    geometry_z.set_axis(axis_no=0, start=-dx, stop=dx, nbins=1)
    geometry_z.set_axis(axis_no=1, start=-dy, stop=dy, nbins=1)
    geometry_z.set_axis(axis_no=2, start=zmin, stop=zmax, nbins=nbins)
    result["z"] = geometry_z

    # 2-D
    geometry_xy = CarthesianMesh()
    geometry_xy.set_axis(axis_no=0, start=xmin, stop=xmax, nbins=nbins)
    geometry_xy.set_axis(axis_no=1, start=ymin, stop=ymax, nbins=nbins)
    geometry_xy.set_axis(axis_no=2, start=-dz, stop=dz, nbins=1)
    result["xy"] = geometry_xy

    geometry_yz = CarthesianMesh()
    geometry_yz.set_axis(axis_no=0, start=-dx, stop=dx, nbins=1)
    geometry_yz.set_axis(axis_no=1, start=ymin, stop=ymax, nbins=nbins)
    geometry_yz.set_axis(axis_no=2, start=zmin, stop=zmax, nbins=nbins)
    result["yz"] = geometry_yz

    geometry_xz = CarthesianMesh()
    geometry_xz.set_axis(axis_no=0, start=xmin, stop=xmax, nbins=nbins)
    geometry_xz.set_axis(axis_no=1, start=-dy, stop=dy, nbins=1)
    geometry_xz.set_axis(axis_no=2, start=zmin, stop=zmax, nbins=nbins)
    result["xz"] = geometry_xz

    # 3-D
    geometry_xyz = CarthesianMesh()
    geometry_xyz.set_axis(axis_no=0, start=xmin, stop=xmax, nbins=nbins)
    geometry_xyz.set_axis(axis_no=1, start=ymin, stop=ymax, nbins=nbins)
    geometry_xyz.set_axis(axis_no=2, start=zmin, stop=zmax, nbins=nbins)
    result["xyz"] = geometry_xyz

    return result


def generate_geomap():
    result = ""

    # create empty estimator object
    estimator = SHEstimator()
    estimator.estimator = SHGeoType.geomap
    estimator.particle_type = SHParticleType.unknown

    # possible detector types and associated names
    det_types = {"zon": SHDetType.zone, "rho": SHDetType.rho, "med": SHDetType.medium}

    # possible geometries and associated names
    geometries_dict = geomap_geometries()
    for geometry_name, det_name in product(geometries_dict, det_types):
        estimator.geometry = geometries_dict[geometry_name]
        estimator.detector_type = det_types[det_name]
        estimator.filename = det_name + "_" + geometry_name
        text = EstimatorWriter.get_text(estimator, add_comment=True)
        result += text

    return result


def main(args=sys.argv[1:]):

    parser = argparse.ArgumentParser()
    parser.add_argument("outputfile", help='output filename path', type=str)
    parsed_args = parser.parse_args(args)

    geomap_text = generate_geomap()

    # open detector.dat file for writing
    with open(parsed_args.outputfile, "w") as f:
        f.write(geomap_text)
        f.write(CardLine.comment + "\n")

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
