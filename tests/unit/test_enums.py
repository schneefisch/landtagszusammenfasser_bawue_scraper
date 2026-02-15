"""Tests for domain enums."""

from bawue_scraper.domain.enums import Dokumententyp, Stationstyp, Vorgangstyp


class TestStationstyp:
    def test_all_values_are_strings(self):
        for member in Stationstyp:
            assert isinstance(member.value, str)

    def test_expected_members_exist(self):
        expected = {
            "preparl-regent",
            "preparl-regbsl",
            "parl-initiativ",
            "parl-ausschber",
            "parl-vollvlsgn",
            "parl-akzeptanz",
            "parl-ablehnung",
            "postparl-vesja",
            "postparl-gsblt",
            "postparl-kraft",
            "sonstig",
        }
        assert {m.value for m in Stationstyp} == expected

    def test_str_comparison(self):
        assert Stationstyp.PARL_INITIATIV == "parl-initiativ"


class TestVorgangstyp:
    def test_all_values_are_strings(self):
        for member in Vorgangstyp:
            assert isinstance(member.value, str)

    def test_expected_members_exist(self):
        expected = {"gg-land-parl", "bw-einsatz", "sonstig"}
        assert {m.value for m in Vorgangstyp} == expected

    def test_str_comparison(self):
        assert Vorgangstyp.GG_LAND_PARL == "gg-land-parl"


class TestDokumententyp:
    def test_all_values_are_strings(self):
        for member in Dokumententyp:
            assert isinstance(member.value, str)

    def test_expected_members_exist(self):
        expected = {
            "preparl-entwurf",
            "entwurf",
            "antrag",
            "anfrage",
            "antwort",
            "mitteilung",
            "beschlussempf",
            "stellungnahme",
            "gutachten",
            "redeprotokoll",
            "tops",
            "tops-aend",
            "tops-ergz",
            "sonstig",
        }
        assert {m.value for m in Dokumententyp} == expected
