import logging

import pytest

from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.readers.shieldhit.reader_base import safe_dettyp, _get_detector_unit


@pytest.mark.smoke
class TestSafeDettyp:

    def test_known_id_roundtrips(self):
        assert safe_dettyp(1) == SHDetType.energy
        assert safe_dettyp(66) == SHDetType.davge
        assert safe_dettyp(67) == SHDetType.dbeta

    def test_unknown_id_warns_and_falls_back_to_invalid(self, caplog):
        with caplog.at_level(logging.WARNING):
            result = safe_dettyp(9999)

        assert result == SHDetType.invalid
        assert any("9999" in record.message for record in caplog.records)
        assert any(record.levelno == logging.WARNING for record in caplog.records)

    def test_negative_id_warns_and_falls_back_to_invalid(self, caplog):
        with caplog.at_level(logging.WARNING):
            result = safe_dettyp(-1)

        assert result == SHDetType.invalid


@pytest.mark.smoke
class TestNewAveragedDetectorUnits:

    def test_davge_dbeta_have_dedicated_units(self):
        assert _get_detector_unit(SHDetType.davge, None) == ("MeV", "Dose-averaged kinetic energy")
        assert _get_detector_unit(SHDetType.dbeta, None) == ("(dimensionless)", "Dose-averaged beta")

    def test_tavge_tbeta_resolve_via_avg_energy_avg_beta_aliases(self):
        # TAVGE/TBETA are aliases of the pre-existing avg_energy/avg_beta members,
        # so they must resolve to the same (already wired-in) unit/name pair.
        assert _get_detector_unit(SHDetType.tavge, None) == _get_detector_unit(SHDetType.avg_energy, None)
        assert _get_detector_unit(SHDetType.tbeta, None) == _get_detector_unit(SHDetType.avg_beta, None)
