from pymchelper.readers.topas import ScoredQuantity, TopasReaderFactory, extract_axis_data, extract_bins_data, extract_parameter_filename, extract_scorer_name, extract_scorer_unit_results

import pytest


@pytest.fixture()
def topas_basic_header() -> str:
    """Return basic Topas header"""
    header = """
# TOPAS Version: 3.9
# Parameter File: minimal.txt
# Results for scorer: FluenceBPprotonsXY
# Filtered by: OnlyIncludeIfIncidentParticlesNamed = 1 "proton"
# Scored in component: PhantomScoringCoarseXY
# X in 4 bins of 0.75 cm
# Y in 4 bins of 0.75 cm
# Z in 1 bin  of 1.75 cm
# Fluence ( /mm2 ) : Mean   Sum   Standard_Deviation
"""
    return header


@pytest.fixture()
def bad_line() -> str:
    """Return corrupted line from Topas header"""
    return "# blah blah: blah"


def test_extract_scorer_name(topas_basic_header: str, bad_line: str):
    good_line = topas_basic_header.splitlines()[3]
    scorer = extract_scorer_name(good_line)
    assert scorer == "FluenceBPprotonsXY"
    scorer = extract_scorer_name(bad_line)
    assert scorer is None


def test_extract_parameter_file(topas_basic_header: str, bad_line: str):
    good_line = topas_basic_header.splitlines()[2]
    assert extract_parameter_filename(good_line) == "minimal.txt"
    assert extract_parameter_filename(bad_line) is None


def test_extract_scored_quantity(topas_basic_header: str, bad_line: str):
    good_line = topas_basic_header.splitlines()[-1]
    scorer = extract_scorer_unit_results(good_line)
    expected_scored_quantity = ScoredQuantity(name="Fluence",
                                              unit="/mm2",
                                              results=["Mean", "Sum", "Standard_Deviation"])
    assert scorer == expected_scored_quantity
    assert extract_scorer_unit_results(bad_line) is None


def test_extract_axis_data(topas_basic_header: str, bad_line: str):
    x_axis_line = topas_basic_header.splitlines()[6]
    y_axis_line = topas_basic_header.splitlines()[7]
    z_axis_line = topas_basic_header.splitlines()[8]
    x_axis = extract_axis_data(x_axis_line)
    assert x_axis.name == "X"
    assert x_axis.num == 4
    assert x_axis.size == 0.75
    assert x_axis.unit == "cm"
    y_axis = extract_axis_data(y_axis_line)
    assert y_axis.name == "Y"
    assert y_axis.num == 4
    assert y_axis.size == 0.75
    assert y_axis.unit == "cm"
    z_axis = extract_axis_data(z_axis_line)
    assert z_axis.name == "Z"
    assert z_axis.num == 1
    assert z_axis.size == 1.75
    assert z_axis.unit == "cm"
    assert extract_axis_data(bad_line) is None
