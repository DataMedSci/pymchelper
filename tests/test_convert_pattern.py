"""Tests for convertmc reading an input pattern with and without --many"""
import json
from pathlib import Path

from pymchelper.run import main


def test_pattern_without_many_merges_into_output_file(main_dir: Path, tmp_path: Path):
    """A quoted pattern without --many merges all matching files into the given output file, same as --many."""
    pattern = str(main_dir / "res" / "shieldhit" / "averaging" / "normalisation-5_aggregation-mean_000*.bdo")
    output_file = tmp_path / "out.json"
    many_dir = tmp_path / "many"

    status_single = main(["json", pattern, str(output_file)])
    status_many = main(["json", "--many", pattern, str(many_dir)])

    assert status_single == 0
    assert status_many == 0
    with open(output_file) as reader:
        merged_single = json.load(reader)
    with open(many_dir / "normalisation-5_aggregation-mean.json") as reader:
        merged_many = json.load(reader)
    assert merged_single == merged_many


def test_pattern_without_matching_files_fails(tmp_path: Path):
    """A pattern which matches no files ends with exit code 1, with and without --many."""
    pattern = str(tmp_path / "nothing_*.bdo")

    status_single = main(["json", pattern, str(tmp_path / "out.json")])
    status_many = main(["json", "--many", pattern, str(tmp_path / "many")])

    assert status_single == 1
    assert status_many == 1


def test_pattern_without_many_unreadable_files_fail(main_dir: Path, tmp_path: Path, monkeypatch):
    """Input files which could not be read end with exit code 1 instead of 0."""
    monkeypatch.setattr("pymchelper.run.convertfromlist", lambda *args, **kwargs: None)
    pattern = str(main_dir / "res" / "shieldhit" / "averaging" / "normalisation-5_aggregation-mean_000*.bdo")

    status = main(["json", pattern, str(tmp_path / "out.json")])

    assert status == 1


def test_pattern_without_many_different_estimators_fail(main_dir: Path, tmp_path: Path):
    """A pattern matching files of different estimators without --many ends with exit code 1, nothing is merged."""
    pattern = str(main_dir / "res" / "shieldhit" / "averaging" / "normalisation-*_aggregation-*_000*.bdo")
    output_file = tmp_path / "out.json"

    status = main(["json", pattern, str(output_file)])

    assert status == 1
    assert not output_file.exists()
