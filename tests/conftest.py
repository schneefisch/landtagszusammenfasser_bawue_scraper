"""Shared test fixtures for the BaWue Scraper test suite."""

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from bawue_scraper.config import Config
from bawue_scraper.domain.enums import Dokumententyp, Stationstyp, Vorgangstyp
from bawue_scraper.domain.models import Autor, Dokument, Gremium, Sitzung, Station, Top, Vorgang


@pytest.fixture()
def config(monkeypatch):
    """Provide a Config instance with test values."""
    monkeypatch.setenv("LTZF_API_URL", "http://localhost:8080")
    monkeypatch.setenv("LTZF_API_KEY", "test-api-key")
    monkeypatch.setenv("COLLECTOR_ID", "test-collector")
    return Config()


@pytest.fixture()
def sample_autor():
    """A sample Autor instance."""
    return Autor(organisation="Fraktion GRÜNE", person="Max Mustermann")


@pytest.fixture()
def sample_gremium():
    """A sample Gremium instance."""
    return Gremium(parlament="BW", name="Ausschuss für Wirtschaft", wahlperiode=17)


@pytest.fixture()
def sample_dokument(sample_autor):
    """A sample Dokument instance."""
    return Dokument(
        titel="Gesetzentwurf der Fraktion GRÜNE",
        volltext="Volltext des Dokuments...",
        hash="abc123hash",
        typ=Dokumententyp.ENTWURF,
        zp_modifiziert=datetime(2026, 2, 1, 10, 0),
        zp_referenz=datetime(2026, 2, 1, 10, 0),
        link="https://www.landtag-bw.de/resource/blob/12345/doc.pdf",
        autoren=[sample_autor],
        drucksnr="17/10266",
    )


@pytest.fixture()
def sample_station(sample_dokument, sample_gremium):
    """A sample Station instance."""
    return Station(
        typ=Stationstyp.PARL_INITIATIV,
        dokumente=[sample_dokument],
        zp_start=datetime(2026, 2, 4, 0, 0),
        gremium=sample_gremium,
    )


@pytest.fixture()
def sample_vorgang(sample_autor, sample_station):
    """A sample Vorgang instance."""
    return Vorgang(
        api_id=uuid4(),
        titel="Gesetz zur Änderung des Landeshochschulgesetzes",
        typ=Vorgangstyp.GG_LAND_PARL,
        wahlperiode=17,
        verfassungsaendernd=False,
        initiatoren=[sample_autor],
        stationen=[sample_station],
        ids=["17/10266"],
    )


@pytest.fixture()
def sample_top():
    """A sample Top instance."""
    return Top(nummer="1", titel="Gesetzentwurf der Landesregierung")


@pytest.fixture()
def sample_sitzung(sample_gremium, sample_top):
    """A sample Sitzung instance."""
    return Sitzung(
        termin=datetime(2026, 2, 5, 9, 0),
        gremium=sample_gremium,
        nummer=141,
        tops=[sample_top],
        public=True,
    )


@pytest.fixture()
def mock_vorgang_source():
    """A mock VorgangSource."""
    return MagicMock()


@pytest.fixture()
def mock_document_extractor():
    """A mock DocumentExtractor."""
    return MagicMock()


@pytest.fixture()
def mock_calendar_source():
    """A mock CalendarSource."""
    return MagicMock()


@pytest.fixture()
def mock_ltzf_api():
    """A mock LtzfApi."""
    return MagicMock()


@pytest.fixture()
def mock_cache():
    """A mock Cache."""
    return MagicMock()
