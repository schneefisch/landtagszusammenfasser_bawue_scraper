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
    def test_erste_beratung_maps_to_vollversammlung(self):
        assert map_stationstyp("Erste Beratung   Plenarprotokoll 17/141 05.02.2026") == Stationstyp.PARL_VOLLVLSGN

    def test_zweite_beratung_maps_to_vollversammlung(self):
        assert map_stationstyp("Zweite Beratung   Plenarprotokoll 17/142 06.02.2026") == Stationstyp.PARL_VOLLVLSGN

    def test_gesetzentwurf_maps_to_initiativ(self):
        assert (
            map_stationstyp("Gesetzentwurf    Fraktion GRÜNE  04.02.2026 Drucksache 17/10266   (13 S.)")
            == Stationstyp.PARL_INITIATIV
        )

    def test_gesetzentwurf_landesregierung_maps_to_preparl_regent(self):
        text = "Gesetzentwurf    Landesregierung  04.02.2026 Drucksache 17/10266"
        assert map_stationstyp(text, initiator="Landesregierung") == Stationstyp.PREPARL_REGENT

    def test_beschlussempfehlung_maps_to_ausschussbericht(self):
        text = "Beschlussempfehlung und Bericht    Ausschuss für Wirtschaft  02.02.2026 Drucksache 17/10210"
        assert map_stationstyp(text) == Stationstyp.PARL_AUSSCHBER

    def test_zustimmung_maps_to_akzeptanz(self):
        assert map_stationstyp("Zustimmung   Plenarprotokoll 17/143") == Stationstyp.PARL_AKZEPTANZ

    def test_ablehnung_maps_to_ablehnung(self):
        assert map_stationstyp("Ablehnung   Plenarprotokoll 17/143") == Stationstyp.PARL_ABLEHNUNG

    def test_ausfertigung_maps_to_vesja(self):
        assert map_stationstyp("Ausfertigung   10.03.2026") == Stationstyp.POSTPARL_VESJA

    def test_gesetzblatt_maps_to_gsblt(self):
        assert map_stationstyp("Gesetzblatt   15.03.2026") == Stationstyp.POSTPARL_GSBLT

    def test_inkrafttreten_maps_to_kraft(self):
        assert map_stationstyp("Inkrafttreten   01.04.2026") == Stationstyp.POSTPARL_KRAFT

    def test_unknown_text_maps_to_sonstig(self):
        assert map_stationstyp("unknown text") == Stationstyp.SONSTIG

    def test_empty_text_maps_to_sonstig(self):
        assert map_stationstyp("") == Stationstyp.SONSTIG

    def test_case_insensitive_matching(self):
        assert map_stationstyp("erste beratung   Plenarprotokoll 17/141") == Stationstyp.PARL_VOLLVLSGN

    def test_map_dict_has_expected_keys(self):
        assert "Gesetzentwurf" in STATIONSTYP_MAP
        assert "Erste Beratung" in STATIONSTYP_MAP
        assert "Ablehnung" in STATIONSTYP_MAP


class TestDokumententypMapping:
    def test_gesetzentwurf_maps_to_entwurf(self):
        assert map_dokumententyp("Gesetzentwurf") == Dokumententyp.ENTWURF

    def test_gesetzentwurf_vorparlamentarisch_maps_to_preparl_entwurf(self):
        assert map_dokumententyp("Gesetzentwurf", is_vorparlamentarisch=True) == Dokumententyp.PREPARL_ENTWURF

    def test_plenarprotokoll_maps_to_redeprotokoll(self):
        assert map_dokumententyp("Plenarprotokoll") == Dokumententyp.REDEPROTOKOLL

    def test_antrag_maps_to_antrag(self):
        assert map_dokumententyp("Antrag") == Dokumententyp.ANTRAG

    def test_kleine_anfrage_maps_to_anfrage(self):
        assert map_dokumententyp("Kleine Anfrage") == Dokumententyp.ANFRAGE

    def test_stellungnahme_maps_to_stellungnahme(self):
        assert map_dokumententyp("Stellungnahme") == Dokumententyp.STELLUNGNAHME

    def test_beschlussempfehlung_maps_to_beschlussempf(self):
        assert map_dokumententyp("Beschlussempfehlung") == Dokumententyp.BESCHLUSSEMPF

    def test_unknown_maps_to_sonstig(self):
        assert map_dokumententyp("unknown") == Dokumententyp.SONSTIG

    def test_empty_maps_to_sonstig(self):
        assert map_dokumententyp("") == Dokumententyp.SONSTIG

    def test_map_dict_has_expected_keys(self):
        assert "Antrag" in DOKUMENTENTYP_MAP
        assert "Plenarprotokoll" in DOKUMENTENTYP_MAP
        assert "Stellungnahme" in DOKUMENTENTYP_MAP
