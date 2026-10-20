import logging
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

import numpy as np
from pymchelper.axis import MeshAxis
from pymchelper.estimator import Estimator
from pymchelper.page import Page
from pymchelper.readers.common import Reader, ReaderFactory

logger = logging.getLogger(__name__)


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


def read_topas_parameters(parameter_file_path: Path, base_directory: Path) -> Optional[Dict[str, str]]:
    """
    Read parameters from a TOPAS parameter file into a dictionary.
    Keys are lower case parameter names without the type, e.g. 'so/demo/numberofhistoriesinrun',
    because TOPAS ignores the case of names. Values are kept as written, e.g. '20' or '"True"'.
    Text after '#' is a comment. Lines without '=' are skipped.
    Files listed in includeFile are read as well, paths are relative to base_directory.
    A parameter set in the including file overrides the same parameter from an included file.
    Returns None if the file or one of the included files does not exist.
    """
    if not parameter_file_path.exists():
        return None

    own_parameters = {}
    include_file_names = []
    with open(parameter_file_path, 'r') as parameter_file:
        for line in parameter_file:
            text_before_comment = line.split('#')[0]
            if '=' not in text_before_comment:
                continue
            name_and_value = text_before_comment.split('=', 1)
            type_and_name = name_and_value[0].strip()
            value = name_and_value[1].strip()
            if type_and_name.lower() == 'includefile':
                include_file_names.extend(value.split())
                continue
            name = type_and_name.split(':')[-1]
            own_parameters[name.lower()] = value

    parameters = {}
    for include_file_name in include_file_names:
        included_parameters = read_topas_parameters(base_directory / include_file_name, base_directory)
        if included_parameters is None:
            return None
        parameters.update(included_parameters)
    parameters.update(own_parameters)
    return parameters


def read_number_of_histories(parameter_file_path: Path) -> int:
    """
    Read the number of histories TOPAS simulated for the given parameter file.
    With several particle sources TOPAS runs as many histories as the source with the largest
    NumberOfHistoriesInRun, the other sources stop generating particles when they reach their own number.
    Returns 0 if the number can't be read from the parameters:
    the parameter file or an included file is missing, no source sets NumberOfHistoriesInRun,
    a source sets it with an expression instead of a plain integer,
    a source reads particles from a phase space file,
    or the histories are not a single run of the sources (time features with several or random times,
    a scorer repeating the run until a statistical limit is reached, results restored from file).
    """
    parameters = read_topas_parameters(parameter_file_path, parameter_file_path.parent)
    if parameters is None:
        return 0

    single_run_values = {
        'tf/numberofsequentialtimes': '1',
        'tf/randomizetimedistribution': '"false"',
        'ts/restoreresultsfromfile': '"false"',
    }
    for name, single_run_value in single_run_values.items():
        value = parameters.get(name, single_run_value)
        if value.lower() != single_run_value:
            return 0

    histories_per_source = []
    for name, value in parameters.items():
        if '/repeatsequenceuntil' in name:
            return 0
        if not name.startswith('so/'):
            continue
        if name.endswith('/type') and value.lower().startswith('"phasespace'):
            return 0
        if name.endswith('/numberofhistoriesinrun'):
            if not value.isdigit():
                return 0
            histories_per_source.append(int(value))

    if not histories_per_source:
        return 0
    return max(histories_per_source)


def extract_bins_data(dimensions: List[str], header_lines: List[str]) -> Optional[Dict]:
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

    def __init__(self, filename: str) -> None:
        super(TopasReader, self).__init__(filename)
        self.directory: Path = Path(filename).parent

    # skipcq: PY-R1000
    def read_data(self, estimator: Estimator) -> bool:
        """
        Read the data from the file and store them in the provided estimator object.
        TOPAS reader assumes that the input file is in the same directory as the output file
        to extract the number of histories from it.
        If the name of the input file is not found in the output file
        or the number of histories can't be read from the input file (see read_number_of_histories),
        the number of histories is set to 0 and the standard deviation is not stored.
        """
        with open(self.filename, 'r') as results_file:
            results_lines = results_file.readlines()
            header_lines = [line for line in results_lines if line.startswith("#")]

            num_histories = 0
            for line in header_lines:
                input_filename = extract_parameter_filename(line)
                if input_filename is not None:
                    input_file_path = Path(self.directory) / input_filename
                    num_histories = read_number_of_histories(input_file_path)
                    break

            estimator.file_corename = Path(self.filename).name[:-4]
            estimator.number_of_primaries = num_histories
            estimator.file_format = "csv"
            estimator.data_order = 'C'  # TOPAS CSV files use C row-major order

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
                    # TOPAS reports the spread of single-history values, the error of the mean is spread / sqrt(N)
                    if estimator.number_of_primaries > 0:
                        page.error_raw = scores / np.sqrt(estimator.number_of_primaries)
                    else:
                        logger.warning("Number of histories not found for %s, standard deviation is skipped",
                                       self.filename)

            # If we didn't find mean results for the scorer, we return False
            if not set_data:
                return False
            estimator.add_page(page)
            return True

    @property
    def corename(self) -> str:
        return self.filename[:-4]
