from pathlib import Path
import re
from typing import List, Tuple, Union

import numpy as np
from pymchelper.axis import MeshAxis
from pymchelper.estimator import Estimator
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
        self.directory = Path(filename).parent

    @staticmethod
    def get_parameter_filename(results_data: str) -> str:
        """Get parameter filename from the output file"""
        parameter_filename = ""
        pattern = r"# Parameter File: (.*)"
        match = re.search(pattern, results_data)
        if match:
            parameter_filename = match.group(1)
        return parameter_filename

    @staticmethod
    def get_bins(dimensions: List[str], results_data: str) -> Union[dict, None]:
        """
        Return dict containing number of bins, bin size and unit for each dimension
        or None if output file does not contain this information for provided dimensions
        """
        bins_data = {}
        pattern = r"# {} in (\d+) bin[s ] of ([\d.]+) (\w+)"
        for dimension in dimensions:
            match = re.search(pattern.format(dimension), results_data)
            if match:
                bins_data[dimension] = {'num': int(match.group(1)),
                                        'size': float(match.group(2)),
                                        'unit': match.group(3)}
            else:
                return None
        return bins_data

    @staticmethod
    def get_scorer_name(results_data: str) -> str:
        """Get scorer name from the output file"""
        name = ""
        pattern = r"# Results for scorer: (\w+)"
        match = re.search(pattern, results_data)
        if match:
            name = match.group(1)
        return name

    @staticmethod
    def get_scorer_unit_results(results_data: str) -> Tuple[str, str, List]:
        """Get scoring quantity, unit and the scoring values (sum/mean/etc.) from the output file"""
        scorers = ['DoseToMedium', 'DoseToWater', 'DoseToMaterial', 'TrackLengthEstimator',
                   'AmbientDoseEquivalent', 'EnergyDeposit', 'Fluence', 'EnergyFluence',
                   'StepCount', 'OpticalPhotonCount', 'OriginCount', 'Charge', 'EffectiveCharge',
                   'ProtonLET', 'SurfaceCurrent', 'SurfaceTrackCount', 'PhaseSpace']
        for scorer in scorers:
            if scorer in results_data:
                unit = ""
                pattern = f"# {scorer}\\s(\\( .*? \\))?\\s*: (.*)"
                match = re.search(pattern, results_data)
                if match:
                    unit = ""
                    if match.group(1):
                        unit = match.group(1)[2:-2]
                    results = match.group(2).split()
                    return scorer, unit, results
        return "", "", []

    @staticmethod
    def get_differential_axis(results_data: str) -> Union[MeshAxis, None]:
        """Check if the output file contains differential axis and get it from file if it does"""
        if "# Binned by" in results_data:
            pattern = r"# Binned by (.+?) in (\d+) bin[s ] of (\d+) (\w+) from ([\d.]+) (\w+) to ([\d.]+) (\w+)"
            match = re.search(pattern, results_data)
            if match:
                binned_by = match.group(1)
                num_bins = int(match.group(2))
                unit = match.group(4)
                min_val = float(match.group(5))
                max_val = float(match.group(7))

                return MeshAxis(n=num_bins, min_val=min_val, max_val=max_val,
                                name=binned_by, unit=unit, binning=MeshAxis.BinningType.linear)
        return None

    def read_data(self, estimator: Estimator) -> bool:
        """
        Read the data from the file and store them in the provided estimator object.
        Topas reader assumes that the input file is in the same directory as the output file
        to extract the number of histories from it - otherwise the number of histories is set to 0.
        """
        with open(self.filename, 'r') as results_file:
            results_data = results_file.read()

            num_histories = 0
            input_filename = TopasReader.get_parameter_filename(results_data)
            input_file_path = Path(self.directory) / input_filename
            if input_file_path.exists():
                with open(input_file_path, 'r') as input_file:
                    pattern = r'NumberOfHistoriesInRun\s*=\s*(\d+)'
                    input_data = input_file.read()
                    match = re.search(pattern, input_data)
                    if match:
                        number_str = re.search(r'\d+', match.group())
                        if number_str:
                            num_histories = int(number_str.group())

            dimensions = [['X', 'Y', 'Z'],
                          ['R', 'Phi', 'Z'],
                          ['Rho', 'Phi', 'Theta']]

            for curr_dimensions in dimensions:
                bins_data = TopasReader.get_bins(curr_dimensions, results_data)
                if bins_data is not None:
                    actual_dimensions = curr_dimensions
                    break

            if bins_data is None:
                return False

            estimator.file_corename = Path(self.filename).name[:-4]
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

            differential_axis = TopasReader.get_differential_axis(results_data)

            # in one output csv file there can be multiple results for one scorer
            # (e.g. sum and mean for fluence)
            scorer, unit, results = TopasReader.get_scorer_unit_results(results_data)
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

                page.title = TopasReader.get_scorer_name(results_data)
                page.name = page.title
                page.dettyp, page.unit = scorer+result, unit

                page.data_raw = scores
                page.error_raw = np.empty_like(page.data_raw)

                estimator.add_page(page)
            return True

    @property
    def corename(self) -> str:
        return self.filename[:-4]
