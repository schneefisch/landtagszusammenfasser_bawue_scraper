"""Tests for the LTZF API client."""

import pytest

from bawue_scraper.adapters.ltzf_client import LtzfClient


class TestLtzfClient:
    def test_instantiation(self, config):
        client = LtzfClient(config)
        assert client._config is config

    def test_submit_vorgang_not_implemented(self, config, sample_vorgang):
        client = LtzfClient(config)
        with pytest.raises(NotImplementedError):
            client.submit_vorgang(sample_vorgang)

    def test_submit_sitzungen_not_implemented(self, config, sample_sitzung):
        from datetime import date

        client = LtzfClient(config)
        with pytest.raises(NotImplementedError):
            client.submit_sitzungen(date(2026, 2, 5), [sample_sitzung])

    # todo: add tests for API key header
    # todo: add tests for HTTP error handling with responses library
    # todo: add tests for rate limiting
