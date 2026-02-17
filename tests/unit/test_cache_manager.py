"""Tests for the file-based cache manager."""

import json

import pytest

from bawue_scraper.adapters.cache_manager import CacheManager
from bawue_scraper.config import Config


@pytest.fixture()
def cache_config(tmp_path, monkeypatch):
    """Config pointing cache_dir at a tmp_path."""
    monkeypatch.setenv("LTZF_API_URL", "http://localhost:8080")
    monkeypatch.setenv("LTZF_API_KEY", "test-api-key")
    monkeypatch.setenv("COLLECTOR_ID", "test-collector")
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    return Config()


class TestCacheManager:
    def test_is_processed_returns_false_for_unknown_id(self, cache_config):
        cache = CacheManager(cache_config)
        assert cache.is_processed("V-12345") is False

    def test_mark_processed_then_is_processed_returns_true(self, cache_config):
        cache = CacheManager(cache_config)
        cache.mark_processed("V-12345")
        assert cache.is_processed("V-12345") is True

    def test_invalidate_removes_from_cache(self, cache_config):
        cache = CacheManager(cache_config)
        cache.mark_processed("V-12345")
        assert cache.is_processed("V-12345") is True
        cache.invalidate("V-12345")
        assert cache.is_processed("V-12345") is False

    def test_invalidate_nonexistent_id_does_not_raise(self, cache_config):
        cache = CacheManager(cache_config)
        cache.invalidate("V-99999")  # should not raise

    def test_persistence_across_instances(self, cache_config):
        cache1 = CacheManager(cache_config)
        cache1.mark_processed("V-12345")
        cache1.mark_processed("V-67890")

        cache2 = CacheManager(cache_config)
        assert cache2.is_processed("V-12345") is True
        assert cache2.is_processed("V-67890") is True
        assert cache2.is_processed("V-00000") is False

    def test_creates_cache_dir_if_missing(self, cache_config):
        from pathlib import Path

        cache_dir = Path(cache_config.cache_dir)
        assert not cache_dir.exists()
        CacheManager(cache_config)
        assert cache_dir.exists()

    def test_handles_empty_cache_file(self, cache_config):
        from pathlib import Path

        cache_dir = Path(cache_config.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "processed.json").write_text("")

        cache = CacheManager(cache_config)
        assert cache.is_processed("V-12345") is False

    def test_handles_corrupt_cache_file(self, cache_config):
        from pathlib import Path

        cache_dir = Path(cache_config.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "processed.json").write_text("{invalid json")

        cache = CacheManager(cache_config)
        assert cache.is_processed("V-12345") is False

    def test_cache_file_contains_json_list(self, cache_config):
        from pathlib import Path

        cache = CacheManager(cache_config)
        cache.mark_processed("V-001")
        cache.mark_processed("V-002")

        data = json.loads((Path(cache_config.cache_dir) / "processed.json").read_text())
        assert set(data) == {"V-001", "V-002"}

    def test_save_uses_atomic_write(self, cache_config, monkeypatch):
        """Verify _save() writes to a temp file then atomically replaces."""
        import os
        from unittest.mock import patch

        cache = CacheManager(cache_config)

        with patch("bawue_scraper.adapters.cache_manager.os.replace", wraps=os.replace) as mock_replace:
            cache.mark_processed("V-001")
            mock_replace.assert_called_once()
            # The target should be the cache file path
            target = mock_replace.call_args[0][1]
            assert str(target) == str(cache._cache_file)
