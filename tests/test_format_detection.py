"""Format detection and rejection of files that are not complete output files"""
from pathlib import Path

import pytest

from pymchelper import run
from pymchelper.input_output import fromfile, guess_reader
from pymchelper.readers.fluka import FlukaReaderFactory

res_dir = Path(__file__).resolve().parent / "res"
bdo2019_file = str(res_dir / "shieldhit" / "v1.0.0" / "ex_yzmsh.bdo")
bdo2019_small_file = str(res_dir / "shieldhit" / "averaging" / "normalisation-5_aggregation-mean_0001.bdo")
bin2010_file = str(res_dir / "shieldhit" / "single" / "ex_yzmsh.bdo")
topas_file = str(res_dir / "topas" / "minimal" / "fluence_bp_protons_xy.csv")


@pytest.mark.parametrize("path, reader_name", [
    (bdo2019_file, "SHReaderBDO2019"),
    (bin2010_file, "SHReaderBin2010"),
    (topas_file, "TopasReader"),
    (str(res_dir / "pld" / "beam_model_generic.csv"), "NoneType"),
],
                         ids=["bdo2019", "bin2010", "topas", "other_csv"])
def test_guess_reader(path: str, reader_name: str):
    """Each format goes to its own reader, other files to none"""
    assert type(guess_reader(path)).__name__ == reader_name


@pytest.mark.parametrize("path", [bdo2019_file, bin2010_file], ids=["bdo2019", "bin2010"])
def test_fluka_probe_rejects_shieldhit(path: str):
    """FLUKA probe says no from the first 4 bytes"""
    assert FlukaReaderFactory(path).get_reader() is None


def test_topas_fromfile():
    """TOPAS CSV is read by fromfile"""
    estimator = fromfile(topas_file)
    assert estimator.pages[0].data_raw.size == 16


@pytest.mark.parametrize("path, fraction", [
    (bdo2019_file, 0.05),
    (bdo2019_file, 0.5),
    (bdo2019_file, 0.9),
    (bdo2019_small_file, 0.5),
    (bdo2019_small_file, 0.99),
    (bin2010_file, 0.5),
    (bin2010_file, 0.99),
],
                         ids=[
                             "bdo2019-5%", "bdo2019-50%", "bdo2019-90%", "bdo2019_small-50%", "bdo2019_small-99%",
                             "bin2010-50%", "bin2010-99%"
                         ])
def test_truncated_file(path: str, fraction: float, tmp_path: Path):
    """A file cut short raises an error naming it"""
    raw = Path(path).read_bytes()
    cut = tmp_path / "cut.bdo"
    cut.write_bytes(raw[:int(len(raw) * fraction)])
    with pytest.raises(ValueError, match="cut.bdo"):
        fromfile(str(cut))


def test_empty_file(tmp_path: Path):
    """An empty file is rejected"""
    empty = tmp_path / "empty.bdo"
    empty.touch()
    with pytest.raises(Exception, match="not compatible"):
        fromfile(str(empty))


def test_convertmc_unreadable_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """convertmc doesn't succeed silently on a file it can't read"""
    monkeypatch.chdir(tmp_path)
    junk = tmp_path / "junk.bdo"
    junk.write_text("\n".join(str(i) for i in range(1, 201)))
    with pytest.raises(Exception, match="junk.bdo"):
        run.main(["json", str(junk), "out.json"])
    assert not (tmp_path / "out.json").exists()


def test_convertmc_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """convertmc returns non-zero and creates nothing for a missing input"""
    monkeypatch.chdir(tmp_path)
    assert run.main(["json", "missing.bdo", "out.json"]) == 1
    assert list(tmp_path.iterdir()) == []
