"""ICS adapter: parses the parliamentary calendar feed."""

from bawue_scraper.config import Config
from bawue_scraper.domain.models import Sitzung
from bawue_scraper.ports.calendar_source import CalendarSource


class IcsAdapter(CalendarSource):
    """Implements CalendarSource by parsing ICS calendar feeds from landtag-bw.de."""

    def __init__(self, config: Config) -> None:
        self._config = config

    def fetch_sessions(self) -> list[Sitzung]:
        """Fetch and parse the ICS calendar into Sitzung objects."""
        # todo: download ICS feed from landtag-bw.de
        # todo: parse VEVENT entries via icalendar library
        # todo: extract date, gremium, metadata
        # todo: build Sitzung objects
        raise NotImplementedError
