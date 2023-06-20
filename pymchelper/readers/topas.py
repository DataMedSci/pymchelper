import os
import re

import numpy as np
from pymchelper.axis import MeshAxis
from pymchelper.page import Page
from pymchelper.readers.common import Reader, ReaderFactory


class TopasReaderFactory(ReaderFactory):
    """Factory for TopasReader"""

    def get_reader(self):
        """Return TopasReader if the file extension is .csv"""
        if self.filename.endswith('.csv'):
            return TopasReader
        return None


class TopasReader(Reader):
    """Reader for Topas output files"""

    def __init__(self, filename):
        super(TopasReader, self).__init__(filename)
        self.directory = os.path.dirname(filename)

    def get_bins(self, dimensions, bins_data, output_data):  # skipcq: PYL-R0201
        """Get number of bins, bin size and unit for each dimension"""
        for dimension in dimensions:
            pattern = f"# {dimension} in (\\d+) bin[s ] of ([\\d.]+) (\\w+)"
            match = re.search(pattern, output_data)
            if match:
                bins_data[dimension] = {'num': int(match.group(1)),
                                        'size': float(match.group(2)),
                                        'unit': match.group(3)}
            else:
                return False
        return True

    def get_scorer_name(self, output_data):  # skipcq: PYL-R0201
        """Get scorer name from the output file"""
        name = ""
        pattern = r"# Results for scorer: (\w+)"
        match = re.search(pattern, output_data)
        if match:
            name = match.group(1)
        return name

    def get_scorer_unit_results(self, output_data):  # skipcq: PYL-R0201
        """Get scoring quantity, unit and the scoring values (sum/mean/etc.) from the output file"""
        scorers = ['DoseToMedium', 'DoseToWater', 'DoseToMaterial', 'TrackLengthEstimator',
                   'AmbientDoseEquivalent', 'EnergyDeposit', 'Fluence', 'EnergyFluence',
                   'StepCount', 'OpticalPhotonCount', 'OriginCount', 'Charge', 'EffectiveCharge',
                   'ProtonLET', 'SurfaceCurrent', 'SurfaceTrackCount', 'PhaseSpace']
        for scorer in scorers:
            if scorer in output_data:
                unit = ""
                pattern = f"# {scorer}\\s(\\( .*? \\))?\\s*: (.*)"
                match = re.search(pattern, output_data)
                if match:
                    unit = ""
                    if match.group(1):
                        unit = match.group(1)[2:-2]
                    results = match.group(2).split()
                    return scorer, unit, results
        return "", "", []

    def get_differential_axis(self, output_data):  # skipcq: PYL-R0201
        """Check if the output file contains differential axis and get it from file if it does"""
        if "# Binned by" in output_data:
            pattern = r"# Binned by (.+?) in (\d+) bin[s ] of (\d+) (\w+) from ([\d.]+) (\w+) to ([\d.]+) (\w+)"
            match = re.search(pattern, output_data)
            if match:
                binned_by = match.group(1)
                num_bins = int(match.group(2))
                unit = match.group(4)
                min_val = float(match.group(5))
                max_val = float(match.group(7))

                return MeshAxis(n=num_bins, min_val=min_val, max_val=max_val,
                                name=binned_by, unit=unit, binning=MeshAxis.BinningType.linear)
        return None

    def read_data(self, estimator):
        """
        Read the data from the file and store them in the provided estimator object.
        Topas reader assumes that the input file is in the same directory as the output file
        to extract the number of histories from it - otherwise the number of histories is set to 0.
        """
        # find the input file to extract the number of histories from it
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

        # generate estimator object for each output file
        with open(self.filename) as output_file:
            output_data = output_file.read()

            bins_data = {}
            dimensions = [['X', 'Y', 'Z'],
                          ['R', 'Phi', 'Z'],
                          ['Rho', 'Phi', 'Theta']]

            for curr_dimensions in dimensions:
                if self.get_bins(curr_dimensions, bins_data, output_data):
                    actual_dimensions = curr_dimensions
                    break

            estimator.file_corename = os.path.basename(self.filename)[:-4]
            estimator.number_of_primaries = num_histories
            estimator.file_format = "csv"
            x_max = bins_data[actual_dimensions[0]]['size']*bins_data[actual_dimensions[0]]['num']
            estimator.x = MeshAxis(n=bins_data[actual_dimensions[0]]['num'],
                                   min_val=0.0, max_val=x_max,
                                   name=actual_dimensions[0], unit=bins_data[actual_dimensions[0]]['unit'],
                                   binning=MeshAxis.BinningType.linear)
            y_max = bins_data[actual_dimensions[1]]['size']*bins_data[actual_dimensions[1]]['num']
            estimator.y = MeshAxis(n=bins_data[actual_dimensions[1]]['num'],
                                   min_val=0.0, max_val=y_max,
                                   name=actual_dimensions[1], unit=bins_data[actual_dimensions[1]]['unit'],
                                   binning=MeshAxis.BinningType.linear)
            z_max = bins_data[actual_dimensions[2]]['size']*bins_data[actual_dimensions[2]]['num']
            estimator.z = MeshAxis(n=bins_data[actual_dimensions[2]]['num'],
                                   min_val=0.0, max_val=z_max,
                                   name=actual_dimensions[2], unit=bins_data[actual_dimensions[2]]['unit'],
                                   binning=MeshAxis.BinningType.linear)

            differential_axis = self.get_differential_axis(output_data)

            # in one output csv file there can be multiple results for one scorer
            # (e.g. sum and mean for fluence)
            scorer, unit, results = self.get_scorer_unit_results(output_data)
            num_results = len(results)
            for column, result in enumerate(results):
                page = Page(estimator=estimator)
                if differential_axis:
                    page.diff_axis1 = differential_axis
                    # when there is a differential axis, each line in csv contains scores
                    # in alternating order. For example, for sum and mean it looks like this:
                    # sum(underflow) mean(underflow) sum(bin1) mean(bin1) sum(bin2) mean(bin2) ...
                    lines = np.genfromtxt(self.filename, delimiter=',')
                    scores = lines[:, column::num_results].flatten()

                else:
                    # when there is no differential axis, each line in csv file looks like this:
                    # x y z result1 result2 result3 ...
                    lines = np.genfromtxt(self.filename, delimiter=',')
                    scores = lines[:, column+3]

                page.title = self.get_scorer_name(output_data)
                page.name = page.title
                page.dettyp, page.unit = scorer+result, unit

                page.data_raw = scores
                page.error_raw = np.empty_like(page.data_raw)

                estimator.add_page(page)
            return True

    @property
    def corename(self):
        return self.filename[:-4]
