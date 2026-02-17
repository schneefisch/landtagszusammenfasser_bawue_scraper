"""Tests for domain models."""

from uuid import uuid4

from bawue_scraper.domain.enums import Vorgangstyp
from bawue_scraper.domain.models import Autor, Gremium, Top, Vorgang


class TestAutor:
    def test_minimal(self):
        autor = Autor(organisation="Fraktion GRÜNE")
        assert autor.organisation == "Fraktion GRÜNE"
        assert autor.person is None

    def test_full(self):
        autor = Autor(organisation="Fraktion GRÜNE", person="Max Mustermann", fachgebiet="Umwelt")
        assert autor.person == "Max Mustermann"


class TestGremium:
    def test_defaults(self):
        gremium = Gremium(name="Plenum")
        assert gremium.parlament == "BW"
        assert gremium.wahlperiode == 17


class TestVorgang:
    def test_creation(self, sample_vorgang):
        assert sample_vorgang.typ == Vorgangstyp.GG_LAND_PARL
        assert sample_vorgang.wahlperiode == 17

    def test_defaults(self, sample_autor, sample_station):
        vorgang = Vorgang(
            api_id=uuid4(),
            titel="Test",
            typ=Vorgangstyp.SONSTIG,
            initiatoren=[sample_autor],
            stationen=[sample_station],
        )
        assert vorgang.verfassungsaendernd is False
        assert vorgang.wahlperiode == 17

    def test_serialization_roundtrip(self, sample_vorgang):
        data = sample_vorgang.model_dump(mode="json")
        restored = Vorgang.model_validate(data)
        assert restored.titel == sample_vorgang.titel


class TestTop:
    def test_minimal(self):
        top = Top(nummer="1", titel="Gesetzentwurf")
        assert top.vorgang_id is None


class TestSitzung:
    def test_creation(self, sample_sitzung):
        assert sample_sitzung.nummer == 141
        assert sample_sitzung.public is True
