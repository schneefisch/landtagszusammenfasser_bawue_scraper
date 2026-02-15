"""Pipeline orchestrator: coordinates the scraping workflow via ports."""

import logging

from bawue_scraper.config import Config
from bawue_scraper.ports.cache import Cache
from bawue_scraper.ports.calendar_source import CalendarSource
from bawue_scraper.ports.document_extractor import DocumentExtractor
from bawue_scraper.ports.ltzf_api import LtzfApi
from bawue_scraper.ports.vorgang_source import VorgangSource

logger = logging.getLogger(__name__)


class Orchestrator:
    """Coordinates the scraping pipeline using injected port implementations."""

    def __init__(
        self,
        config: Config,
        vorgang_source: VorgangSource,
        document_extractor: DocumentExtractor,
        calendar_source: CalendarSource,
        ltzf_api: LtzfApi,
        cache: Cache,
    ) -> None:
        self._config = config
        self._vorgang_source = vorgang_source
        self._document_extractor = document_extractor
        self._calendar_source = calendar_source
        self._ltzf_api = ltzf_api
        self._cache = cache

    def run(self) -> None:
        """Execute a full scraping cycle.

        Steps:
        1. For each Vorgangstyp, search PARLIS for Vorgänge
        2. For each new Vorgang (not in cache):
           a. Extract text from associated PDFs
           b. Map PARLIS enums to LTZF enums
           c. Submit to LTZF backend
           d. Mark as processed in cache
        3. Fetch and submit calendar/session data
        """
        # todo: implement scraping cycle per Vorgangstyp
        # todo: handle errors per-Vorgang without stopping the full run
        # todo: fetch and submit calendar data
        # todo: log progress and statistics
        raise NotImplementedError

    def run_vorgaenge(self) -> None:
        """Scrape and submit Vorgänge only."""
        # todo: implement Vorgang-only pipeline
        raise NotImplementedError

    def run_kalender(self) -> None:
        """Scrape and submit calendar/session data only."""
        # todo: implement calendar-only pipeline
        raise NotImplementedError
