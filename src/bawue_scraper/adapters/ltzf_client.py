"""LTZF client: submits collected data to the LTZF backend API."""

from datetime import date

from bawue_scraper.config import Config
from bawue_scraper.domain.models import Sitzung, Vorgang
from bawue_scraper.ports.ltzf_api import LtzfApi


class LtzfClient(LtzfApi):
    """Implements LtzfApi by calling the LTZF REST API."""

    def __init__(self, config: Config) -> None:
        self._config = config
        # todo: initialize requests.Session with X-API-Key header

    def submit_vorgang(self, vorgang: Vorgang) -> bool:
        """Submit a Vorgang via PUT /api/v2/vorgang."""
        # todo: serialize Vorgang to JSON
        # todo: PUT to {ltzf_api_url}/api/v2/vorgang
        # todo: handle HTTP errors and rate limiting
        raise NotImplementedError

    def submit_sitzungen(self, datum: date, sitzungen: list[Sitzung]) -> bool:
        """Submit Sitzungen via PUT /api/v2/kalender/BW/{datum}."""
        # todo: serialize Sitzungen to JSON
        # todo: PUT to {ltzf_api_url}/api/v2/kalender/BW/{datum}
        # todo: handle HTTP errors and rate limiting
        raise NotImplementedError
