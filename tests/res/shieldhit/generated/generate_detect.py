import argparse
import os
import sys
from collections import OrderedDict
from itertools import product

# import necessary code pieces from pymchelper
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator import SHEstimator
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.shieldhit.detector.fortran_card import EstimatorWriter, CardLine
from pymchelper.shieldhit.detector.geometry import CarthesianMesh, Zone, Plane, CylindricalMesh
from pymchelper.shieldhit.particle import SHParticleType


def zone_geometries():
    result = OrderedDict()

    geometry1 = Zone()
    geometry1.start = 1
    result["z1"] = geometry1

    geometry2 = Zone()
    geometry2.start = 1
    geometry2.stop = 3
    result["z13"] = geometry2

    geometry3 = Zone()
    geometry3.start = 2
    geometry3.stop = 3
    result["z23"] = geometry3

    return result


def plane_geometries():
    result = OrderedDict()

    geometry1 = Plane()
    geometry1.set_point(0., 0., 5.)
    geometry1.set_normal(0., 0., 1.)
    result["p1"] = geometry1

    geometry2 = Plane()
    geometry2.set_point(0., 0., 5.)
    geometry2.set_normal(0., 0., -1.)
    result["p2"] = geometry2

    geometry3 = Plane()
    geometry3.set_point(0., 0., 0.)
    geometry3.set_normal(0., 0., 1.)
    result["p3"] = geometry3

    geometry4 = Plane()
    geometry4.set_point(0., 0., 5.)
    geometry4.set_normal(0., 1., 0.)
    result["p4"] = geometry4

    return result


def general_geometries(geo_class,
                       nbins=10,
                       xmin=-20.0,
                       xmax=20.0,
                       ymin=-20.0,
                       ymax=20.0,
                       zmin=-10.0,
                       zmax=30.0,
                       dx=1.0,
                       dy=1.0,
                       dz=1.0):
    result = OrderedDict()

    xmid = (xmin + xmax) / 2.0
    ymid = (ymin + ymax) / 2.0
    zmid = (zmin + zmax) / 2.0

    # 1-D
    geometry_x = geo_class()
    geometry_x.set_axis(axis_no=0, start=xmin, stop=xmax, nbins=nbins)
    geometry_x.set_axis(axis_no=1, start=ymid - dy, stop=ymid + dy, nbins=1)
    geometry_x.set_axis(axis_no=2, start=zmid - dz, stop=zmid + dz, nbins=1)
    result["x"] = geometry_x

    geometry_y = geo_class()
    geometry_y.set_axis(axis_no=0, start=xmid - dx, stop=xmid + dx, nbins=1)
    geometry_y.set_axis(axis_no=1, start=ymin, stop=ymax, nbins=nbins)
    geometry_y.set_axis(axis_no=2, start=zmid - dz, stop=zmid + dz, nbins=1)
    result["y"] = geometry_y

    geometry_z = geo_class()
    geometry_z.set_axis(axis_no=0, start=-dx, stop=xmid + dx, nbins=1)
    geometry_z.set_axis(axis_no=1, start=ymid - dy, stop=ymid + dy, nbins=1)
    geometry_z.set_axis(axis_no=2, start=zmin, stop=zmax, nbins=nbins)
    result["z"] = geometry_z

    # 2-D
    geometry_xy = geo_class()
    geometry_xy.set_axis(axis_no=0, start=xmin, stop=xmax, nbins=nbins)
    geometry_xy.set_axis(axis_no=1, start=ymin, stop=ymax, nbins=nbins)
    geometry_xy.set_axis(axis_no=2, start=zmid - dz, stop=zmid + dz, nbins=1)
    result["xy"] = geometry_xy

    geometry_yz = geo_class()
    geometry_yz.set_axis(axis_no=0, start=xmid - dx, stop=xmid + dx, nbins=1)
    geometry_yz.set_axis(axis_no=1, start=ymin, stop=ymax, nbins=nbins)
    geometry_yz.set_axis(axis_no=2, start=zmin, stop=zmax, nbins=nbins)
    result["yz"] = geometry_yz

    geometry_xz = geo_class()
    geometry_xz.set_axis(axis_no=0, start=xmin, stop=xmax, nbins=nbins)
    geometry_xz.set_axis(axis_no=1, start=ymid - dy, stop=ymid + dy, nbins=1)
    geometry_xz.set_axis(axis_no=2, start=zmin, stop=zmax, nbins=nbins)
    result["xz"] = geometry_xz

    # 3-D
    geometry_xyz = geo_class()
    geometry_xyz.set_axis(axis_no=0, start=xmin, stop=xmax, nbins=nbins)
    geometry_xyz.set_axis(axis_no=1, start=ymin, stop=ymax, nbins=nbins)
    geometry_xyz.set_axis(axis_no=2, start=zmin, stop=zmax, nbins=nbins)
    result["xyz"] = geometry_xyz

    return result


def msh_geometries():
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

    result = OrderedDict()

    # 0-D
    geometry = CarthesianMesh()
    geometry.set_axis(axis_no=0, start=-dx, stop=dx, nbins=1)
    geometry.set_axis(axis_no=1, start=-dy, stop=dy, nbins=1)
    geometry.set_axis(axis_no=2, start=5.0, stop=6.0, nbins=1)
    result["0"] = geometry

    general = general_geometries(
        CarthesianMesh,
        nbins=nbins,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        zmin=zmin,
        zmax=zmax,
        dx=dx,
        dy=dy,
        dz=dz)

    result.update(general)

    return result


def cyl_geometries():
    nbins = 10
    xmin = 0.0
    xmax = 10.0
    ymin = 0.0
    ymax = 3.14
    zmin = -10.0
    zmax = 30.0
    dx = 1.0
    dy = 0.2
    dz = 1.0

    result = OrderedDict()

    # 0-D
    geometry = CylindricalMesh()
    geometry.set_axis(axis_no=0, start=0.0, stop=dx, nbins=1)
    geometry.set_axis(axis_no=1, start=0.0, stop=dy, nbins=1)
    geometry.set_axis(axis_no=2, start=5.0, stop=6.0, nbins=1)
    result["0"] = geometry

    general = general_geometries(
        CylindricalMesh,
        nbins=nbins,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        zmin=zmin,
        zmax=zmax,
        dx=dx,
        dy=dy,
        dz=dz)

    result.update(general)

    return result


def generate_geomap():
    result = ""

    # create empty estimator object
    estimator = SHEstimator()
    estimator.estimator = SHGeoType.geomap
    estimator.particle_type = SHParticleType.unknown

    # possible detector types and associated names
    det_types = OrderedDict({"zon": SHDetType.zone, "rho": SHDetType.rho, "med": SHDetType.medium})

    # possible geometries and associated names
    geometries_dict = msh_geometries()
    for geometry_name, det_name in product(geometries_dict, det_types):
        estimator.geometry = geometries_dict[geometry_name]
        estimator.detector_type = det_types[det_name]
        estimator.filename = det_name + "_" + geometry_name
        text = EstimatorWriter.get_text(estimator, add_comment=True)
        result += text

    return result


def generate_mesh(geometry_function, estimator_type):
    result = ""

    # create empty estimator object
    estimator = SHEstimator()
    estimator.estimator = estimator_type

    # possible particle types and associated names
    part_types = OrderedDict({"al": SHParticleType.all, "p": SHParticleType.proton, "n": SHParticleType.neutron})

    # possible detector types and associated names
    det_types = OrderedDict({"en": SHDetType.energy,
                             "fl": SHDetType.fluence,
                             "aen": SHDetType.avg_energy,
                             "bet": SHDetType.avg_beta})

    # possible geometries and associated names
    geometries_dict = geometry_function()
    for geometry_name, part_name, det_name in product(geometries_dict, part_types, det_types):
        estimator.geometry = geometries_dict[geometry_name]
        estimator.detector_type = det_types[det_name]
        estimator.particle_type = part_types[part_name]
        estimator.filename = det_name + "_" + geometry_name + "_" + part_name
        text = EstimatorWriter.get_text(estimator, add_comment=True)
        result += text

    return result


def generate_zone():
    result = ""

    # create empty estimator object
    estimator = SHEstimator()
    estimator.estimator = SHGeoType.zone

    # possible particle types and associated names
    part_types = OrderedDict({"al": SHParticleType.all, "p": SHParticleType.proton, "n": SHParticleType.neutron})

    # possible detector types and associated names
    det_types = OrderedDict({"en": SHDetType.energy,
                             "fl": SHDetType.fluence,
                             "aen": SHDetType.avg_energy,
                             "bet": SHDetType.avg_beta})

    # possible geometries and associated names
    geometries_dict = zone_geometries()
    for geometry_name, part_name, det_name in product(geometries_dict, part_types, det_types):
        estimator.geometry = geometries_dict[geometry_name]
        estimator.detector_type = det_types[det_name]
        estimator.particle_type = part_types[part_name]
        estimator.filename = det_name + "_" + geometry_name + "_" + part_name
        text = EstimatorWriter.get_text(estimator, add_comment=True)
        result += text

    return result


def generate_plane():
    result = ""

    # create empty estimator object
    estimator = SHEstimator()
    estimator.estimator = SHGeoType.plane

    # possible particle types and associated names
    part_types = OrderedDict({"al": SHParticleType.all, "p": SHParticleType.proton, "n": SHParticleType.neutron})

    # possible detector types and associated names
    det_types = OrderedDict({"cnt": SHDetType.counter})

    # possible geometries and associated names
    geometries_dict = plane_geometries()
    for geometry_name, part_name, det_name in product(geometries_dict, part_types, det_types):
        estimator.geometry = geometries_dict[geometry_name]
        estimator.detector_type = det_types[det_name]
        estimator.particle_type = part_types[part_name]
        estimator.filename = det_name + "_" + geometry_name + "_" + part_name
        text = EstimatorWriter.get_text(estimator, add_comment=True)
        result += text

    return result


def save_file(dirname, filename, content):
    fullpath = os.path.join(dirname, filename)
    with open(fullpath, "w") as f:
        f.write(CardLine.credits + "\n")
        f.write(content)
        f.write(CardLine.comment + "\n")


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument("outputdir", help='output directory', type=str)
    parsed_args = parser.parse_args(args)

    geomap_text = generate_geomap()
    save_file(parsed_args.outputdir, "detect_geomap.dat", geomap_text)

    msh_text = generate_mesh(geometry_function=msh_geometries, estimator_type=SHGeoType.msh)
    save_file(parsed_args.outputdir, "detect_msh.dat", msh_text)

    cyl_text = generate_mesh(geometry_function=cyl_geometries, estimator_type=SHGeoType.cyl)
    save_file(parsed_args.outputdir, "detect_cyl.dat", cyl_text)

    zone_text = generate_zone()
    save_file(parsed_args.outputdir, "detect_zone.dat", zone_text)

    plane_text = generate_plane()
    save_file(parsed_args.outputdir, "detect_plane.dat", plane_text)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
