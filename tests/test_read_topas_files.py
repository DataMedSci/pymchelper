import os

import numpy as np
from pymchelper.estimator import Estimator
import pymchelper.flair.Input as Input
from pymchelper.readers.topas import TopasReaderFactory


def test_read():
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
    assert estimator.pages[0].dettyp == "Fluence"
    assert estimator.pages[0].unit == "/mm2"
    
    assert estimator.pages[0].data.shape == (4, 4, 1, 1, 1)
    
    expected_data = [0.00177, 0., 0., 0.00088,
                0.00088, 0.00177, 0., 0.00088,
                0.00266, 0.00088, 0.00177, 0.00177,
                0.00088, 0., 0., 0.]
    assert np.allclose(estimator.pages[0].data_raw, expected_data, atol=1e-5)
    
def test_cylindrical_coordinates():
    file_path = os.path.join("tests", "res", "topas", "cylinder", "MyScorer.csv")
    
    reader = TopasReaderFactory(file_path).get_reader()
    assert reader is not None
    
    reader = reader(file_path)
    estimator = Estimator()
    reader.read_data(estimator)
    
    assert estimator.x.name == "R"
    assert estimator.y.name == "Phi"
    assert estimator.z.name == "Z"
    
    assert estimator.pages[0].dettyp == "SurfaceTrackCount"