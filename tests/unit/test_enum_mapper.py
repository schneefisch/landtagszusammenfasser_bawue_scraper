"""Tests for the PARLIS→LTZF enum mapper."""

from bawue_scraper.domain.enums import Dokumententyp, Stationstyp, Vorgangstyp
from bawue_scraper.mapping.enum_mapper import (
    DOKUMENTENTYP_MAP,
    STATIONSTYP_MAP,
    VORGANGSTYP_MAP,
    map_dokumententyp,
    map_stationstyp,
    map_vorgangstyp,
)


class TestVorgangstypMapping:
    def test_gesetzgebung_maps_to_gg_land_parl(self):
        assert map_vorgangstyp("Gesetzgebung") == Vorgangstyp.GG_LAND_PARL

    def test_haushaltsgesetzgebung_maps_to_gg_land_parl(self):
        assert map_vorgangstyp("Haushaltsgesetzgebung") == Vorgangstyp.GG_LAND_PARL

    def test_volksantrag_maps_to_gg_land_parl(self):
        assert map_vorgangstyp("Volksantrag") == Vorgangstyp.GG_LAND_PARL

    def test_kleine_anfrage_maps_to_sonstig(self):
        assert map_vorgangstyp("Kleine Anfrage") == Vorgangstyp.SONSTIG

    def test_unknown_maps_to_sonstig(self):
        assert map_vorgangstyp("Unbekannter Typ") == Vorgangstyp.SONSTIG

    def test_map_has_all_known_types(self):
        expected_keys = {
            "Gesetzgebung",
            "Haushaltsgesetzgebung",
            "Volksantrag",
            "Antrag",
            "Kleine Anfrage",
            "Große Anfrage",
            "Mündliche Anfrage",
            "Aktuelle Debatte",
            "Regierungserklärung/Regierungsinformation",
            "Untersuchungsausschuss",
        }
        assert set(VORGANGSTYP_MAP.keys()) == expected_keys


class TestStationstypMapping:
    """Tests for map_stationstyp — regex logic is stubbed, so these test the stub fallback."""

    def test_stub_returns_sonstig(self):
        # todo: update these tests when regex logic is implemented
        assert map_stationstyp("Erste Beratung") == Stationstyp.SONSTIG

    def test_map_dict_has_expected_keys(self):
        assert "Gesetzentwurf" in STATIONSTYP_MAP
        assert "Erste Beratung" in STATIONSTYP_MAP
        assert "Ablehnung" in STATIONSTYP_MAP


class TestDokumententypMapping:
    """Tests for map_dokumententyp — regex logic is stubbed, so these test the stub fallback."""

    def test_stub_returns_sonstig(self):
        # todo: update these tests when regex logic is implemented
        assert map_dokumententyp("Gesetzentwurf") == Dokumententyp.SONSTIG

    def test_map_dict_has_expected_keys(self):
        assert "Antrag" in DOKUMENTENTYP_MAP
        assert "Plenarprotokoll" in DOKUMENTENTYP_MAP
        assert "Stellungnahme" in DOKUMENTENTYP_MAP
