import os

import numpy as np
from pymchelper.estimator import Estimator
from pymchelper.readers.topas import TopasReaderFactory


def test_read():
    """Test if Topas output file is read correctly"""
    file_path = os.path.join("tests", "res", "topas", "minimal", "fluence_bp_protons_xy.csv")
    
    reader = TopasReaderFactory(file_path).get_reader()
    assert reader is not None
    
    reader = reader(file_path)
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
    assert estimator.pages[0].dettyp == "FluenceMean"
    assert estimator.pages[0].unit == "/mm2"
    
    assert estimator.pages[0].data.shape == (4, 4, 1, 1, 1)
    
    expected_data_sum = [0.00177, 0., 0., 0.00088,
                0.00088, 0.00177, 0., 0.00088,
                0.00266, 0.00088, 0.00177, 0.00177,
                0.00088, 0., 0., 0.]
    expected_data_mean = [0.0053739, 0., 0., 0.00373801, 0.00501473, 0.00606808,
                0., 0.00382928, 0.00655932, 0.00400361, 0.00571516, 0.00537066,
                0.00353209, 0., 0., 0.]
    assert np.allclose(estimator.pages[0].data_raw, expected_data_sum, atol=1e-5)
    assert np.allclose(estimator.pages[1].data_raw, expected_data_mean, atol=1e-5)


def test_cylindrical_coordinates():
    """Test reading of cylindrical coordinates"""
    file_path = os.path.join("tests", "res", "topas", "cylinder", "MyScorer.csv")
    
    reader = TopasReaderFactory(file_path).get_reader()
    assert reader is not None
    
    reader = reader(file_path)
    estimator = Estimator()
    reader.read_data(estimator)
    
    assert estimator.x.name == "R"
    assert estimator.y.name == "Phi"
    assert estimator.z.name == "Z"
    
    assert estimator.pages[0].dettyp == "SurfaceTrackCountSum"


def test_differential_axis():
    """Test reading of optional differential axis"""
    file_path = os.path.join("tests", "res", "topas", "binning_by_energy", "fluence_bp_protons_xy.csv")
    
    reader = TopasReaderFactory(file_path).get_reader()
    assert reader is not None
    
    reader = reader(file_path)
    estimator = Estimator()
    reader.read_data(estimator)
    
    assert estimator.pages[0].dimension == 3
    assert estimator.pages[0].diff_axis1.name == "incident track energy"
    assert estimator.pages[0].diff_axis1.unit == "MeV"
    assert estimator.pages[0].diff_axis1.n == 10
    assert estimator.pages[0].diff_axis1.min_val == 0
    assert estimator.pages[0].diff_axis1.max_val == 100
    
    expected_data_mean = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.080903509193889e-11, 9.013105463113584e-11,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.083960132124552e-11, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.152689792517148e-11, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.821172892712442e-10, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.067865282717259e-11, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.696254032024574e-10, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.006026509227903e-11, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.811402691690857e-10, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.147425086196995e-11, 9.013259427045676e-11,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.07914094811693e-11, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    expected_data_std = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.285797997168091e-10, 3.959436365570868e-10, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 3.996723026036162e-10, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 4.199542091279842e-10, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.349932203318999e-10, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 3.993406336962584e-10, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 6.575561083882781e-10, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 2.921940838136542e-10, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 5.669806053760889e-10, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 4.084218326124751e-10, 3.962953306540497e-10, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.012494671211039e-10, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,]
    assert estimator.pages[0].dettyp == "DoseToMediumMean"
    assert np.allclose(estimator.pages[0].data_raw, expected_data_mean, atol=1e-5)
    assert estimator.pages[1].dettyp == "DoseToMediumStandard_Deviation"
    assert np.allclose(estimator.pages[1].data_raw, expected_data_std, atol=1e-5)