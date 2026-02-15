"""Tests for the file-based cache manager."""

import pytest

from bawue_scraper.adapters.cache_manager import CacheManager


class TestCacheManager:
    def test_instantiation(self, config):
        cache = CacheManager(config)
        assert cache._config is config

    def test_is_processed_not_implemented(self, config):
        cache = CacheManager(config)
        with pytest.raises(NotImplementedError):
            cache.is_processed("V-12345")

    def test_mark_processed_not_implemented(self, config):
        cache = CacheManager(config)
        with pytest.raises(NotImplementedError):
            cache.mark_processed("V-12345")

    def test_invalidate_not_implemented(self, config):
        cache = CacheManager(config)
        with pytest.raises(NotImplementedError):
            cache.invalidate("V-12345")

    # todo: add tests for file-based persistence
    # todo: add tests for cache invalidation
