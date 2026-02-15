"""Port: parliamentary calendar / session data source."""

from abc import ABC, abstractmethod

from bawue_scraper.domain.models import Sitzung


class CalendarSource(ABC):
    """Provides parliamentary session and calendar data."""

    @abstractmethod
    def fetch_sessions(self) -> list[Sitzung]:
        """Fetch all available parliamentary sessions.

        Returns:
            A list of Sitzung objects.
        """
