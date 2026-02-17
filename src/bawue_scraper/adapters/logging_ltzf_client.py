"""Dry-run LTZF client: logs submissions without making HTTP calls."""

import logging
from datetime import date

from bawue_scraper.domain.models import Sitzung, Vorgang
from bawue_scraper.ports.ltzf_api import LtzfApi

logger = logging.getLogger(__name__)


class LoggingLtzfClient(LtzfApi):
    """Logs Vorgang/Sitzung submissions instead of sending them (dry-run mode)."""

    def submit_vorgang(self, vorgang: Vorgang) -> bool:
        logger.info("[DRY-RUN] Would submit Vorgang: %s (id=%s)", vorgang.titel, vorgang.api_id)
        return True

    def submit_sitzungen(self, datum: date, sitzungen: list[Sitzung]) -> bool:
        logger.info("[DRY-RUN] Would submit %d Sitzungen for %s", len(sitzungen), datum)
        return True
