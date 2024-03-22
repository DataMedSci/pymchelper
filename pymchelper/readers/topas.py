from pathlib import Path
import re
from typing import List, Optional, Tuple

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


def get_topas_estimators(output_files_path: str) -> List[Estimator]:
    """Get Topas estimators from provided directory"""
    estimators_list = []
    for path in Path(output_files_path).iterdir():
        topas_reader = TopasReaderFactory(str(path)).get_reader()
        if topas_reader:
            reader = topas_reader(path)
            estimator = Estimator()
            reader.read(estimator)
            estimators_list.append(estimator)

    return estimators_list


def extract_parameter_filename(header_line: str) -> Optional[str]:
    """Get parameter filename from the output file"""
    pattern = r"# Parameter File: (.*)"
    match = re.search(pattern, header_line)
    parameter_filename = None
    if match:
        parameter_filename = match.group(1)
    return parameter_filename


def extract_bins_data(dimensions: List[str], header_lines: List[str]) -> Optional[dict]:
    """
    Takes as arguments a list of dimensions (e.g. ['X', 'Y', 'Z'])
    and three consecutive lines from the output file header.
    Returns dict containing number of bins, bin size and unit for each dimension
    or None if output file does not contain this information for provided dimensions
    """
    if len(dimensions) != 3 or len(header_lines) != 3:
        return None
    bins_data = {}
    pattern = r"# {} in (\d+) bin[s ] of ([\d.]+) (\w+)"
    for line_index, dimension in enumerate(dimensions):
        match = re.search(pattern.format(dimension), header_lines[line_index])
        if match:
            bins_data[dimension] = {'num': int(match.group(1)), 'size': float(match.group(2)), 'unit': match.group(3)}
        else:
            return None
    return bins_data


def extract_scorer_name(header_line: str) -> Optional[str]:
    """Get scorer name from the output file"""
    pattern = r"# Results for scorer: (\w+)"
    match = re.search(pattern, header_line)
    name = None
    if match:
        name = match.group(1)
    return name


def extract_scorer_unit_results(header_line: str) -> Optional[Tuple[str, str, List]]:
    """Get scoring quantity, unit and the scoring values (sum/mean/etc.) from the output file"""
    scorers = [
        'DoseToMedium', 'DoseToWater', 'DoseToMaterial', 'TrackLengthEstimator', 'AmbientDoseEquivalent',
        'EnergyDeposit', 'Fluence', 'EnergyFluence', 'StepCount', 'OpticalPhotonCount', 'OriginCount', 'Charge',
        'EffectiveCharge', 'ProtonLET', 'SurfaceCurrent', 'SurfaceTrackCount', 'PhaseSpace'
    ]
    for scorer in scorers:
        if scorer in header_line:
            unit = ""
            pattern = f"# {scorer}\\s(\\( .*? \\))?\\s*: (.*)"
            match = re.search(pattern, header_line)
            if match:
                unit = ""
                if match.group(1):
                    unit = match.group(1)[2:-2]
                results = match.group(2).split()
                return (scorer, unit, results)
    return None


def extract_differential_axis(header_line: str) -> Optional[MeshAxis]:
    """Check if the output file contains differential axis and get it from file if it does"""
    if "# Binned by" in header_line:
        pattern = r"# Binned by (.+?) in (\d+) bin[s ] of (\d+) (\w+) from ([\d.]+) (\w+) to ([\d.]+) (\w+)"
        match = re.search(pattern, header_line)
        if match:
            binned_by = match.group(1)
            num_bins = int(match.group(2))
            unit = match.group(4)
            min_val = float(match.group(5))
            max_val = float(match.group(7))

            return MeshAxis(n=num_bins,
                            min_val=min_val,
                            max_val=max_val,
                            name=binned_by,
                            unit=unit,
                            binning=MeshAxis.BinningType.linear)
    return None


class TopasReader(Reader):
    """Reader for Topas output files"""

    def __init__(self, filename):
        super(TopasReader, self).__init__(filename)
        self.directory = Path(filename).parent

    # skipcq: PY-R1000
    def read_data(self, estimator: Estimator) -> bool:
        """
        Read the data from the file and store them in the provided estimator object.
        TOPAS reader assumes that the input file is in the same directory as the output file
        to extract the number of histories from it.
        If the name of the input file is not found in the output file
        or the input file is not in the same directory, the number of histories is set to 0.
        """
        with open(self.filename, 'r') as results_file:
            results_lines = results_file.readlines()
            header_lines = [line for line in results_lines if line.startswith("#")]

            num_histories = 0
            for line in header_lines:
                input_filename = extract_parameter_filename(line)
                if input_filename is not None:
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
                    break

            estimator.file_corename = Path(self.filename).name[:-4]
            estimator.number_of_primaries = num_histories
            estimator.file_format = "csv"

            dimensions = [['X', 'Y', 'Z'], ['R', 'Phi', 'Z'], ['R', 'Phi', 'Theta']]

            actual_dimensions = None
            for curr_dimensions in dimensions:
                for line_index in range(len(header_lines) - 3):
                    bins_data = extract_bins_data(curr_dimensions, header_lines[line_index:line_index + 3])
                    if bins_data is not None:
                        actual_dimensions = curr_dimensions
                        x_max = bins_data[actual_dimensions[0]]['size'] * bins_data[actual_dimensions[0]]['num']
                        estimator.x = MeshAxis(n=bins_data[actual_dimensions[0]]['num'],
                                               min_val=0.0,
                                               max_val=x_max,
                                               name=actual_dimensions[0],
                                               unit=bins_data[actual_dimensions[0]]['unit'],
                                               binning=MeshAxis.BinningType.linear)
                        y_max = bins_data[actual_dimensions[1]]['size'] * bins_data[actual_dimensions[1]]['num']
                        estimator.y = MeshAxis(n=bins_data[actual_dimensions[1]]['num'],
                                               min_val=0.0,
                                               max_val=y_max,
                                               name=actual_dimensions[1],
                                               unit=bins_data[actual_dimensions[1]]['unit'],
                                               binning=MeshAxis.BinningType.linear)
                        z_max = bins_data[actual_dimensions[2]]['size'] * bins_data[actual_dimensions[2]]['num']
                        estimator.z = MeshAxis(n=bins_data[actual_dimensions[2]]['num'],
                                               min_val=0.0,
                                               max_val=z_max,
                                               name=actual_dimensions[2],
                                               unit=bins_data[actual_dimensions[2]]['unit'],
                                               binning=MeshAxis.BinningType.linear)
                        no_bins = False
                        break
                if actual_dimensions is not None:
                    break

            if bins_data is None:
                # We assume that the geometry is not divided into bins
                # (or in other words there is one bin with one score)
                no_bins = True

            for line in header_lines:
                differential_axis = extract_differential_axis(line)
                if differential_axis is not None:
                    break

            # In one output csv file there can be multiple results for one scorer
            # (e.g. mean and standard deviation for fluence).
            # We look for mean and standard deviation and ignore the rest.
            # Then we put them in raw_data and raw_error respectively.
            scorer, unit, results = None, None, None
            for line in header_lines:
                res = extract_scorer_unit_results(line)
                if res is not None:
                    scorer, unit, results = res
                    break

            # We did not find scorer info in the output file
            if scorer is None:
                return False

            num_results = len(results)
            page = Page(estimator=estimator)
            set_data = False
            for column, result in enumerate(results):
                if result not in ['Mean', 'Standard_Deviation']:
                    continue
                if differential_axis:
                    page.diff_axis1 = differential_axis
                    # When there is a differential axis, each line in csv contains scores
                    # in alternating order. For example, for sum and mean it looks like this:
                    # sum(underflow) mean(underflow) sum(bin1) mean(bin1) sum(bin2) mean(bin2) ...
                    # Binning by time has one additional bin at the end : overflow.
                    # Binning by energy has two additional bins at the end:
                    # overflow and for case of no incident track.
                    # Both have one additional bin at the beginning: underflow.
                    # We ignore these additional bins.
                    if differential_axis.name == 'time':
                        additional_bins = 1
                    elif differential_axis.name == 'incident track energy':
                        additional_bins = 2
                    else:
                        return False
                    lines = np.genfromtxt(self.filename, delimiter=',')
                    last_bin_index = len(lines[0]) - num_results * additional_bins
                    scores = lines[:, column + num_results:last_bin_index:num_results].flatten()

                else:
                    # When there is no differential axis, each line in csv file looks like this:
                    # x y z result1 result2 result3 ...
                    # where x, y, z are coordinates of the bin - we ignore them.
                    # Unless there are no bins - then there is one line with scores
                    # result1 result2 ...
                    if no_bins:
                        data = np.genfromtxt(self.filename, delimiter=',')
                        if data.shape == ():
                            scores = np.array([data])
                        else:
                            scores = np.array([data[column]])
                    else:
                        lines = np.genfromtxt(self.filename, delimiter=',')
                        scores = lines[:, column + 3]

                for line in header_lines:
                    title = extract_scorer_name(line)
                    if title is not None:
                        page.title = title
                        page.name = title
                        break

                page.dettyp, page.unit = scorer, unit

                if result == 'Mean':
                    page.data_raw = scores
                    set_data = True
                elif result == 'Standard_Deviation':
                    page.error_raw = scores

            # If we didn't find mean results for the scorer, we return False
            if not set_data:
                return False
            estimator.add_page(page)
            return True

    @property
    def corename(self) -> str:
        return self.filename[:-4]
