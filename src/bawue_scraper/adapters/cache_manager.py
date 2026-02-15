"""File-based cache manager for tracking processed Vorgänge."""

from bawue_scraper.config import Config
from bawue_scraper.ports.cache import Cache


class CacheManager(Cache):
    """Implements Cache using file-based storage (no external dependencies)."""

    def __init__(self, config: Config) -> None:
        self._config = config
        # todo: initialize cache directory and load existing state

    def is_processed(self, vorgang_id: str) -> bool:
        """Check if a Vorgang has already been processed."""
        # todo: look up vorgang_id in persistent file-based cache
        raise NotImplementedError

    def mark_processed(self, vorgang_id: str) -> None:
        """Mark a Vorgang as processed."""
        # todo: persist vorgang_id to cache file
        raise NotImplementedError

    def invalidate(self, vorgang_id: str) -> None:
        """Remove a Vorgang from the cache for re-processing."""
        # todo: remove vorgang_id from cache file
        raise NotImplementedError
