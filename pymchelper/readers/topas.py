import os
import re

import numpy as np
from pymchelper.axis import MeshAxis
from pymchelper.estimator import Estimator
from pymchelper.page import Page
from pymchelper.readers.common import Reader, ReaderFactory


class TopasReaderFactory(ReaderFactory):
    def get_reader(self):
        if self.filename.endswith('.csv'):
            return TopasReader
        return None
    
class TopasReader(Reader):
    def __init__(self, filename):
        self.filename = filename
        self.directory = os.path.dirname(filename)

    def get_bins(self, dimensions, bins_data, output_data):
        for dimension in dimensions:
            pattern = f"# {dimension} in (\\d+) bin[s ] of ([\\d.]+) (\\w+)"
            match = re.search(pattern, output_data)
            if match:
                bins_data[dimension] = {'num': int(match.group(1)), 'size': float(match.group(2)), 'unit': match.group(3)}
            else:
                return False
        return True
    
    def get_scorer_name(self, output_data):
        name = ""
        pattern = f"# Results for scorer: (\\w+)"
        match = re.search(pattern, output_data)
        if match:
            name = match.group(1)
        return name
    
    def get_scorer_and_unit(self, output_data):
        scorers = ['DoseToMedium', 'DoseToWater', 'DoseToMaterial', 'TrackLengthEstimator',
                   'AmbientDoseEquivalent', 'EnergyDeposit', 'Fluence', 'EnergyFluence',
                   'StepCount', 'OpticalPhotonCount', 'OriginCount', 'Charge', 'EffectiveCharge',
                   'ProtonLET', 'SurfaceCurrent', 'SurfaceTrackCount', 'PhaseSpace']
        for scorer in scorers:
            if scorer in output_data:
                unit = ""
                pattern = f"# {scorer} \\( (.*?) \\)"
                match = re.search(pattern, output_data)
                if match:
                    unit = match.group(1)
                return scorer, unit

    def read_data(self, estimator):
        """
        Read the data from the file and store them in the provided estimator object.
        Topas reader assumes that the input file is in the same directory as the output file
        to extract the number of histories from it - otherwise the number of histories is set to 0.
        """

        #find the input file to extract the number of histories from it
        num_histories = 0
        for input_file in os.listdir(self.directory):
            if input_file.endswith(".txt"):
                input_file_path = os.path.join(self.directory, input_file)
                with open(input_file_path) as input_file:
                    pattern = r'NumberOfHistoriesInRun\s*=\s*(\d+)'
                    num_histories = 0
                    input_data = input_file.read()
                    match = re.search(pattern, input_data)
                    if match:
                        number_str = re.search(r'\d+', match.group())
                        if number_str:
                            num_histories = int(number_str.group())
        
        #generate estimator object for each output file
        with open(self.filename) as output_file:
            output_data  = output_file.read()
            
            bins_data = {}
            dimensions = [['X', 'Y', 'Z'],
                          ['R', 'Phi', 'Z'],
                          ['Rho', 'Phi', 'Theta']]
            
            for curr_dimensions in dimensions:
                if self.get_bins(curr_dimensions, bins_data, output_data):
                    actual_dimensions = curr_dimensions
                    break
        
            lines = np.genfromtxt(self.filename, delimiter=',')
            scores = lines[:, 3]

            estimator.file_corename = os.path.basename(self.filename)[:-4]
            estimator.number_of_primaries = num_histories
            estimator.file_format = "csv"
            estimator.x = MeshAxis(n=bins_data[actual_dimensions[0]]['num'], min_val=0.0, max_val=bins_data[actual_dimensions[0]]['size']*bins_data[actual_dimensions[0]]['num'],
                                name=actual_dimensions[0], unit=bins_data[actual_dimensions[0]]['unit'], binning=MeshAxis.BinningType.linear)
            estimator.y = MeshAxis(n=bins_data[actual_dimensions[1]]['num'], min_val=0.0, max_val=bins_data[actual_dimensions[1]]['size']*bins_data[actual_dimensions[1]]['num'],
                                    name=actual_dimensions[1], unit=bins_data[actual_dimensions[1]]['unit'], binning=MeshAxis.BinningType.linear)
            estimator.z = MeshAxis(n=bins_data[actual_dimensions[2]]['num'], min_val=0.0, max_val=bins_data[actual_dimensions[2]]['size']*bins_data[actual_dimensions[2]]['num'],
                                    name=actual_dimensions[2], unit=bins_data[actual_dimensions[2]]['unit'], binning=MeshAxis.BinningType.linear)
            
            page = Page(estimator=estimator)
            
            page.title = self.get_scorer_name(output_data)
            page.name = page.title
            page.dettyp, page.unit = self.get_scorer_and_unit(output_data)

            page.data_raw = scores
            page.error_raw = np.empty_like(page.data_raw)

            estimator.add_page(page)
            return True
            

    @property
    def corename(self):
        return self.filename[:-4]