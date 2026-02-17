"""LTZF client: submits collected data to the LTZF backend API."""

import logging
from datetime import date

import requests

from bawue_scraper.config import Config
from bawue_scraper.domain.models import Sitzung, Vorgang
from bawue_scraper.ports.ltzf_api import LtzfApi

logger = logging.getLogger(__name__)


class LtzfClient(LtzfApi):
    """Implements LtzfApi by calling the LTZF REST API."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-API-Key": config.ltzf_api_key,
                "X-Scraper-Id": config.collector_id,
                "Content-Type": "application/json",
            }
        )
        if not config.ltzf_allow_redirects:
            self._session.max_redirects = 0

    def submit_vorgang(self, vorgang: Vorgang) -> bool:
        """Submit a Vorgang via PUT /api/v2/vorgang."""
        url = f"{self._config.ltzf_api_url}/api/v2/vorgang"
        body = vorgang.model_dump(mode="json", exclude_none=True)

        try:
            resp = self._session.put(url, json=body)
            if resp.status_code in (201, 409):
                return True
            logger.error("Failed to submit Vorgang %s: HTTP %s", vorgang.titel, resp.status_code)
            return False
        except requests.ConnectionError as e:
            logger.error("Cannot reach LTZF API at %s: %s", url, e)
            return False
        except requests.RequestException:
            logger.exception("Request error submitting Vorgang %s", vorgang.titel)
            return False

    def submit_sitzungen(self, datum: date, sitzungen: list[Sitzung]) -> bool:
        """Submit Sitzungen via PUT /api/v2/kalender/BW/{datum}."""
        raise NotImplementedError
