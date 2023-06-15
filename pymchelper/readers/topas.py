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
            bins_data = {}
            output_data  = output_file.read()
            for dimension in ['X', 'Y', 'Z']:
                pattern = f"# {dimension} in (\\d+) bin[s ] of ([\\d.]+) (\\w+)"
                match = re.search(pattern, output_data)
                if match:
                    bins_data[dimension] = {'num': int(match.group(1)), 'size': float(match.group(2)), 'unit': match.group(3)}
        
        lines = np.genfromtxt(self.filename, delimiter=',')
        scores = lines[:, 3]

        estimator.file_corename = os.path.basename(self.filename)[:-4]
        estimator.number_of_primaries = num_histories
        estimator.file_format = "csv"
        estimator.x = MeshAxis(n=bins_data['X']['num'], min_val=0.0, max_val=bins_data['X']['size']*bins_data['X']['num'],
                            name="X", unit=bins_data['X']['unit'], binning=MeshAxis.BinningType.linear)
        estimator.y = MeshAxis(n=bins_data['Y']['num'], min_val=0.0, max_val=bins_data['Y']['size']*bins_data['Y']['num'],
                                name="Y", unit=bins_data['Y']['unit'], binning=MeshAxis.BinningType.linear)
        estimator.z = MeshAxis(n=bins_data['Z']['num'], min_val=0.0, max_val=bins_data['Z']['size']*bins_data['Z']['num'],
                                name="Z", unit=bins_data['Z']['unit'], binning=MeshAxis.BinningType.linear)
        
        page = Page(estimator=estimator)
        #TODO
        page.title = ""
        page.name = ""
        page.unit = ""

        page.data_raw = scores
        page.error_raw = np.empty_like(page.data_raw)

        estimator.add_page(page)
        return True
            

    @property
    def corename(self):
        return self.filename[:-4]