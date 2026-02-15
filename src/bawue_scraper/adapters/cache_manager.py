"""File-based cache manager for tracking processed Vorgänge."""

import json
import logging
from pathlib import Path

from bawue_scraper.config import Config
from bawue_scraper.ports.cache import Cache

logger = logging.getLogger(__name__)


class CacheManager(Cache):
    """Implements Cache using file-based storage (no external dependencies)."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._cache_dir = Path(config.cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file = self._cache_dir / "processed.json"
        self._processed: set[str] = self._load()

    def _load(self) -> set[str]:
        if not self._cache_file.exists():
            return set()
        try:
            text = self._cache_file.read_text(encoding="utf-8")
            if not text.strip():
                return set()
            data = json.loads(text)
            return set(data)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Corrupt cache file %s, starting fresh", self._cache_file)
            return set()

    def _save(self) -> None:
        self._cache_file.write_text(
            json.dumps(sorted(self._processed), ensure_ascii=False),
            encoding="utf-8",
        )

    def is_processed(self, vorgang_id: str) -> bool:
        """Check if a Vorgang has already been processed."""
        return vorgang_id in self._processed

    def mark_processed(self, vorgang_id: str) -> None:
        """Mark a Vorgang as processed."""
        self._processed.add(vorgang_id)
        self._save()

    def invalidate(self, vorgang_id: str) -> None:
        """Remove a Vorgang from the cache for re-processing."""
        self._processed.discard(vorgang_id)
        self._save()
