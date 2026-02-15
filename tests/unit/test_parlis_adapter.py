"""Tests for the PARLIS adapter."""

import pytest

from bawue_scraper.adapters.parlis_adapter import ParlisAdapter


class TestParlisAdapter:
    def test_instantiation(self, config):
        adapter = ParlisAdapter(config)
        assert adapter._config is config

    def test_search_not_implemented(self, config):
        adapter = ParlisAdapter(config)
        with pytest.raises(NotImplementedError):
            from datetime import date

            adapter.search("Gesetzgebung", date(2026, 1, 1), date(2026, 2, 1))

    def test_get_detail_not_implemented(self, config):
        adapter = ParlisAdapter(config)
        with pytest.raises(NotImplementedError):
            adapter.get_detail("V-12345")

    # todo: add tests for session management
    # todo: add tests for search query construction
    # todo: add tests for HTML parsing with mocked responses
    # todo: add tests for Fundstellen parsing
    # todo: add tests for pagination
    # todo: add tests for date range subdivision
