"""Port: cache for tracking processed items."""

from abc import ABC, abstractmethod


class Cache(ABC):
    """Tracks already-processed items to avoid redundant work."""

    @abstractmethod
    def is_processed(self, vorgang_id: str) -> bool:
        """Check if a Vorgang has already been processed.

        Args:
            vorgang_id: The identifier of the Vorgang.

        Returns:
            True if already processed, False otherwise.
        """

    @abstractmethod
    def mark_processed(self, vorgang_id: str) -> None:
        """Mark a Vorgang as processed.

        Args:
            vorgang_id: The identifier of the Vorgang.
        """

    @abstractmethod
    def invalidate(self, vorgang_id: str) -> None:
        """Remove a Vorgang from the processed cache (for re-processing).

        Args:
            vorgang_id: The identifier of the Vorgang.
        """
