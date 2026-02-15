"""PARLIS adapter: fetches Vorgang data from the BaWue parliament's PARLIS system."""

from datetime import date

from bawue_scraper.config import Config
from bawue_scraper.ports.vorgang_source import VorgangSource


class ParlisAdapter(VorgangSource):
    """Implements VorgangSource by scraping the PARLIS API."""

    def __init__(self, config: Config) -> None:
        self._config = config
        # todo: initialize requests.Session with PARLIS cookies

    def search(self, vorgangstyp: str, date_from: date, date_to: date) -> list[dict]:
        """Search PARLIS for Vorgänge matching the given criteria."""
        # todo: establish session (cookies/referer)
        # todo: POST browse.tt.json with search query
        # todo: handle "status: running" → subdivide date range
        # todo: GET report.tt.html with pagination
        # todo: parse HTML records
        # todo: parse Fundstellen text
        raise NotImplementedError

    def get_detail(self, vorgang_id: str) -> dict:
        """Fetch detailed data for a single Vorgang from PARLIS."""
        # todo: fetch and parse detail page
        raise NotImplementedError
