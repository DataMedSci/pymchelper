from pathlib import Path
import numpy as np
from typing import Generator
from pymchelper.estimator import Estimator
from pymchelper.readers.topas import TopasReaderFactory

import pytest

@pytest.fixture()
def main_dir() -> Generator[Path, None, None]:
    """Return path to main directory"""
    yield Path(__file__).resolve().parent

@pytest.fixture()
def topas_minimal_output_path(main_dir) -> Generator[Path, None, None]:
    """Return path to Topas minimal output file"""
    yield main_dir / "res" / "topas" / "minimal" / "fluence_bp_protons_xy.csv"

@pytest.fixture()
def topas_cylinder_output_path(main_dir) -> Generator[Path, None, None]:
    """Return path to Topas output file with cylindrical coordinates"""
    yield main_dir / "res" / "topas" / "cylinder" / "MyScorer.csv"

@pytest.fixture()
def topas_binning_by_energy_output_path(main_dir) -> Generator[Path, None, None]:
    """Return path to Topas output file with binning by energy"""
    yield main_dir / "res" / "topas" / "binning_by_energy" / "fluence_bp_protons_xy.csv"

@pytest.fixture()
def topas_sphere_binned_by_time_path(main_dir) -> Generator[Path, None, None]:
    """Return path to Topas output file with binning by energy"""
    yield main_dir / "res" / "topas" / "sphere" / "MyScorer.csv"

@pytest.fixture()
def topas_no_bins_path(main_dir) -> Generator[Path, None, None]:
    """Return path to Topas output file without any bins"""
    yield main_dir / "res" / "topas" / "no_bins" / "MyScorer.csv"

def test_read(topas_minimal_output_path: Path):
    """Test if Topas output file is read correctly"""
    reader = TopasReaderFactory(str(topas_minimal_output_path)).get_reader()
    assert reader is not None
    
    reader = reader(str(topas_minimal_output_path))
    estimator = Estimator()
    reader.read_data(estimator)
    assert estimator.number_of_primaries == 20
    assert estimator.file_corename == "fluence_bp_protons_xy"
    assert estimator.dimension == 2
    
    assert estimator.x.name == "X"
    assert estimator.x.n == 4
    assert estimator.y.name == "Y"
    assert estimator.y.n == 4
    assert estimator.z.name == "Z"
    assert estimator.z.n == 1
    
    assert estimator.pages[0].name == "FluenceBPprotonsXY"
    assert estimator.pages[0].title == "FluenceBPprotonsXY"
    assert estimator.pages[0].dettyp == "Fluence"
    assert estimator.pages[0].unit == "/mm2"
    
    assert estimator.pages[0].data.shape == (4, 4, 1, 1, 1)
    
    expected_data_mean = [0.00177, 0., 0., 0.00088,
                0.00088, 0.00177, 0., 0.00088,
                0.00266, 0.00088, 0.00177, 0.00177,
                0.00088, 0., 0., 0.]
    expected_data_std = [0.0053739 , 0., 0., 0.00384373,
                .00475825, 0.00592593, 0., 0.00353209,
                0.00642803, 0.00378469, 0.00628262, 0.00505895,
                0.00353209, 0., 0., 0.]
    assert np.allclose(estimator.pages[0].data_raw, expected_data_mean, atol=1e-5)
    assert np.allclose(estimator.pages[0].error_raw, expected_data_std, atol=1e-5)


def test_cylindrical_coordinates(topas_cylinder_output_path: Path):
    """Test reading of cylindrical coordinates"""
    reader = TopasReaderFactory(str(topas_cylinder_output_path)).get_reader()
    assert reader is not None
    
    reader = reader(str(topas_cylinder_output_path))
    estimator = Estimator()
    reader.read_data(estimator)
    
    assert estimator.x.name == "R"
    assert estimator.y.name == "Phi"
    assert estimator.z.name == "Z"
    
    assert estimator.pages[0].dettyp == "SurfaceTrackCount"


def test_differential_axis(topas_binning_by_energy_output_path: Path):
    """Test reading of optional differential axis"""
    reader = TopasReaderFactory(str(topas_binning_by_energy_output_path)).get_reader()
    assert reader is not None
    
    reader = reader(str(topas_binning_by_energy_output_path))
    estimator = Estimator()
    reader.read_data(estimator)
    
    assert estimator.pages[0].dimension == 3
    assert estimator.pages[0].diff_axis1.name == "incident track energy"
    assert estimator.pages[0].diff_axis1.unit == "MeV"
    assert estimator.pages[0].diff_axis1.n == 10
    assert estimator.pages[0].diff_axis1.min_val == 0
    assert estimator.pages[0].diff_axis1.max_val == 100
    
    expected_data_mean = [ 0.0, 0.0, 0.0, 0.0, 9.080903509193889e-11, 9.013105463113584e-11 ]
    expected_data_std = [ 0.0, 0.0, 0.0, 0.0, 4.285797997168091e-10, 3.959436365570868e-10 ]
    assert estimator.pages[0].dettyp == "DoseToMedium"
    assert len(estimator.pages[0].data_raw) == 160
    assert np.allclose(estimator.pages[0].data_raw[0:6], expected_data_mean, atol=1e-5)
    assert len(estimator.pages[0].error_raw) == 160
    assert np.allclose(estimator.pages[0].error_raw[0:6], expected_data_std, atol=1e-5)


def test_sphere_bin_by_time(topas_sphere_binned_by_time_path: Path):
    """Test reading of spherical coordinates and binning by time"""
    reader = TopasReaderFactory(str(topas_sphere_binned_by_time_path)).get_reader()
    assert reader is not None

    reader = reader(str(topas_sphere_binned_by_time_path))
    estimator = Estimator()
    reader.read_data(estimator)

    assert estimator.x.name == "R"
    assert estimator.y.name == "Phi"
    assert estimator.z.name == "Theta"

    assert estimator.pages[0].dimension == 3
    assert estimator.pages[0].diff_axis1.name == "time"
    assert estimator.pages[0].diff_axis1.unit == "ns"
    assert estimator.pages[0].diff_axis1.n == 10
    assert estimator.pages[0].diff_axis1.min_val == 0
    assert estimator.pages[0].diff_axis1.max_val == 100

    expected_data_mean = [ 0.0, 0.1, 0.0, 0.0]
    assert estimator.pages[0].dettyp == "SurfaceTrackCount"
    assert len(estimator.pages[0].data_raw) == 40
    assert np.allclose(estimator.pages[0].data_raw[0:4], expected_data_mean, atol=1e-5)
    
def test_no_bins(topas_no_bins_path: Path):
    """Test reading of Topas output file without any bins"""
    reader = TopasReaderFactory(str(topas_no_bins_path)).get_reader()
    assert reader is not None

    reader = reader(str(topas_no_bins_path))
    estimator = Estimator()
    reader.read_data(estimator)

    assert estimator.pages[0].dimension == 0

    expected_data_mean = [0.1]
    assert estimator.pages[0].dettyp == "SurfaceTrackCount"
    assert len(estimator.pages[0].data_raw) == 1
    assert np.allclose(estimator.pages[0].data_raw, expected_data_mean, atol=1e-5)