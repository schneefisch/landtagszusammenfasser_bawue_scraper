"""Port: source of legislative proceedings (Vorgänge)."""

from abc import ABC, abstractmethod
from datetime import date


class VorgangSource(ABC):
    """Fetches raw Vorgang data from a parliamentary data source."""

    @abstractmethod
    def search(self, vorgangstyp: str, date_from: date, date_to: date) -> list[dict]:
        """Search for Vorgänge matching the given criteria.

        Args:
            vorgangstyp: The PARLIS Vorgangstyp to search for.
            date_from: Start of the date range.
            date_to: End of the date range.

        Returns:
            A list of raw Vorgang dictionaries.
        """

    @abstractmethod
    def get_detail(self, vorgang_id: str) -> dict:
        """Fetch detailed data for a single Vorgang.

        Args:
            vorgang_id: The identifier of the Vorgang.

        Returns:
            A dictionary with detailed Vorgang data.
        """
