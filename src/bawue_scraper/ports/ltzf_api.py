"""Port: LTZF backend API for submitting collected data."""

from abc import ABC, abstractmethod
from datetime import date

from bawue_scraper.domain.models import Sitzung, Vorgang


class LtzfApi(ABC):
    """Submits scraped data to the LTZF backend."""

    @abstractmethod
    def submit_vorgang(self, vorgang: Vorgang) -> bool:
        """Submit a Vorgang to the LTZF backend via PUT /api/v2/vorgang.

        Args:
            vorgang: The Vorgang to submit.

        Returns:
            True if submission succeeded, False otherwise.
        """

    @abstractmethod
    def submit_sitzungen(self, datum: date, sitzungen: list[Sitzung]) -> bool:
        """Submit Sitzungen for a date via PUT /api/v2/kalender/{parlament}/{datum}.

        Args:
            datum: The date for the sessions.
            sitzungen: The sessions to submit.

        Returns:
            True if submission succeeded, False otherwise.
        """
