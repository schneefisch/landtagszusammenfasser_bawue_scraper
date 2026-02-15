"""Tests for the ICS calendar adapter."""

import pytest

from bawue_scraper.adapters.ics_adapter import IcsAdapter


class TestIcsAdapter:
    def test_instantiation(self, config):
        adapter = IcsAdapter(config)
        assert adapter._config is config

    def test_fetch_sessions_not_implemented(self, config):
        adapter = IcsAdapter(config)
        with pytest.raises(NotImplementedError):
            adapter.fetch_sessions()

    # todo: add tests for ICS parsing with sample .ics data
    # todo: add tests for VEVENT → Sitzung mapping
