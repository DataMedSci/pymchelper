"""Format detection and rejection of files that are not complete output files"""
from pathlib import Path

import pytest

from pymchelper import run
from pymchelper.estimator import Estimator
from pymchelper.input_output import fromfile, guess_reader
from pymchelper.readers.fluka import FlukaReaderFactory
from pymchelper.readers.shieldhit.reader_base import read_next_token
from pymchelper.readers.shieldhit.reader_bdo2019 import SHReaderBDO2019
from pymchelper.readers.shieldhit.reader_bin2010 import SHReaderBin2010
from pymchelper.readers.topas import TopasReader

res_dir = Path(__file__).resolve().parent / "res"
bdo2019_file = str(res_dir / "shieldhit" / "v1.0.0" / "ex_yzmsh.bdo")
bdo2019_small_file = str(res_dir / "shieldhit" / "averaging" / "normalisation-5_aggregation-mean_0001.bdo")
bin2010_file = str(res_dir / "shieldhit" / "single" / "ex_yzmsh.bdo")
topas_file = str(res_dir / "topas" / "minimal" / "fluence_bp_protons_xy.csv")


@pytest.mark.parametrize("path, reader_class", [
    pytest.param(bdo2019_file, SHReaderBDO2019, id="bdo2019"),
    pytest.param(bin2010_file, SHReaderBin2010, id="bin2010"),
    pytest.param(topas_file, TopasReader, id="topas"),
])
def test_guess_reader(path: str, reader_class: type):
    """Each format goes to its own reader"""
    assert isinstance(guess_reader(path), reader_class)


def test_guess_reader_other_csv():
    """A CSV file not written by TOPAS gets no reader"""
    assert guess_reader(str(res_dir / "pld" / "beam_model_generic.csv")) is None


@pytest.mark.parametrize("path", [
    pytest.param(bdo2019_file, id="bdo2019"),
    pytest.param(bin2010_file, id="bin2010"),
])
def test_fluka_probe_rejects_shieldhit(path: str):
    """FLUKA probe says no from the first 4 bytes"""
    assert FlukaReaderFactory(path).get_reader() is None


def test_topas_fromfile():
    """TOPAS CSV is read by fromfile"""
    estimator = fromfile(topas_file)
    assert estimator.pages[0].data_raw.size == 16


@pytest.mark.parametrize("path, fraction", [
    pytest.param(bdo2019_file, 0.05, id="bdo2019-5%"),
    pytest.param(bdo2019_file, 0.5, id="bdo2019-50%"),
    pytest.param(bdo2019_file, 0.9, id="bdo2019-90%"),
    pytest.param(bdo2019_small_file, 0.5, id="bdo2019_small-50%"),
    pytest.param(bdo2019_small_file, 0.99, id="bdo2019_small-99%"),
    pytest.param(bin2010_file, 0.5, id="bin2010-50%"),
    pytest.param(bin2010_file, 0.99, id="bin2010-99%"),
])
def test_truncated_file(path: str, fraction: float, tmp_path: Path):
    """A file cut short raises an error naming it"""
    raw = Path(path).read_bytes()
    cut = tmp_path / "cut.bdo"
    cut.write_bytes(raw[:int(len(raw) * fraction)])
    with pytest.raises(ValueError, match="cut.bdo"):
        fromfile(str(cut))


def token_ends(path: str) -> list:
    """Byte offsets where each token of a BDO file ends, the last one being the end of the file"""
    offsets = []
    with open(path, "rb") as f:
        # skip the fixed-size file header: magic bytes, endianness marker and version string
        f.seek(24)
        while read_next_token(f) is not None:
            offsets.append(f.tell())
    return offsets


@pytest.mark.parametrize("path", [
    pytest.param(bdo2019_file, id="bdo2019"),
    pytest.param(bdo2019_small_file, id="bdo2019_small"),
])
def test_bdo2019_cut_between_tokens(path: str, tmp_path: Path):
    """A BDO2019 file cut between two tokens is rejected by the reader, wherever the cut is"""
    raw = Path(path).read_bytes()
    offsets = token_ends(path)
    offsets_before_end = offsets[:-1]
    cut = tmp_path / "cut.bdo"
    for cut_at in offsets_before_end:
        cut.write_bytes(raw[:cut_at])
        with pytest.raises(ValueError, match="cut.bdo"):
            SHReaderBDO2019(str(cut)).read(Estimator())


def test_bdo2019_corrupted_token_type(tmp_path: Path):
    """A token with an unknown payload type is rejected instead of being read as the end of the file"""
    raw = bytearray(Path(bdo2019_file).read_bytes())
    # debug token opening the second page; its 8-byte payload type follows the 8-byte token id
    token_start = 241832
    type_start = token_start + 8
    raw[type_start:type_start + 8] = b"XXXXXXXX"
    corrupted = tmp_path / "corrupted.bdo"
    corrupted.write_bytes(bytes(raw))
    with pytest.raises(ValueError, match="unknown payload type"):
        fromfile(str(corrupted))


def test_topas_reader_truncated_file(tmp_path: Path):
    """A TOPAS CSV with missing rows is rejected by the reader"""
    lines = Path(topas_file).read_text().splitlines(keepends=True)
    lines_without_last = lines[:-1]
    cut = tmp_path / "cut.csv"
    cut.write_text("".join(lines_without_last))
    with pytest.raises(ValueError, match="cut.csv"):
        TopasReader(str(cut)).read(Estimator())


def test_empty_file(tmp_path: Path):
    """An empty file is rejected"""
    empty = tmp_path / "empty.bdo"
    empty.touch()
    with pytest.raises(ValueError, match="not compatible"):
        fromfile(str(empty))


def test_convertmc_unreadable_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
    """convertmc logs a one-line error and returns non-zero for a file it can't read"""
    monkeypatch.chdir(tmp_path)
    junk = tmp_path / "junk.bdo"
    junk.write_text("\n".join(str(i) for i in range(1, 201)))
    assert run.main(["json", str(junk), "out.json"]) == 1
    assert "File format not compatible" in caplog.text
    assert "junk.bdo" in caplog.text
    assert not (tmp_path / "out.json").exists()


def test_convertmc_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """convertmc returns non-zero and creates nothing for a missing input"""
    monkeypatch.chdir(tmp_path)
    assert run.main(["json", "missing.bdo", "out.json"]) == 1
    assert list(tmp_path.iterdir()) == []
