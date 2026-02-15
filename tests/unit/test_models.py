"""Tests for domain models."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from bawue_scraper.domain.enums import Dokumententyp, Stationstyp, Vorgangstyp
from bawue_scraper.domain.models import Autor, Dokument, Gremium, Station, Top, Vorgang


class TestAutor:
    def test_minimal(self):
        autor = Autor(organisation="Fraktion GRÜNE")
        assert autor.organisation == "Fraktion GRÜNE"
        assert autor.person is None

    def test_full(self):
        autor = Autor(organisation="Fraktion GRÜNE", person="Max Mustermann", fachgebiet="Umwelt")
        assert autor.person == "Max Mustermann"

    def test_organisation_required(self):
        with pytest.raises(ValidationError):
            Autor()


class TestGremium:
    def test_defaults(self):
        gremium = Gremium(name="Plenum")
        assert gremium.parlament == "BW"
        assert gremium.wahlperiode == 17

    def test_name_required(self):
        with pytest.raises(ValidationError):
            Gremium()


class TestDokument:
    def test_creation(self, sample_dokument):
        assert sample_dokument.typ == Dokumententyp.ENTWURF
        assert sample_dokument.drucksnr == "17/10266"

    def test_required_fields(self):
        with pytest.raises(ValidationError):
            Dokument(titel="Test")


class TestStation:
    def test_creation(self, sample_station):
        assert sample_station.typ == Stationstyp.PARL_INITIATIV
        assert len(sample_station.dokumente) == 1

    def test_optional_fields_default_none(self, sample_dokument, sample_gremium):
        station = Station(
            typ=Stationstyp.SONSTIG,
            dokumente=[sample_dokument],
            zp_start=datetime(2026, 1, 1),
            gremium=sample_gremium,
        )
        assert station.titel is None
        assert station.schlagworte is None


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

    def test_with_vorgang_id(self):
        vid = uuid4()
        top = Top(nummer="2", titel="Anfrage", vorgang_id=vid)
        assert top.vorgang_id == vid


class TestSitzung:
    def test_creation(self, sample_sitzung):
        assert sample_sitzung.nummer == 141
        assert sample_sitzung.public is True
