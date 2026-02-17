"""Integration tests for LTZF API client — requires a running LTZF backend."""

import pytest

from bawue_scraper.adapters.ltzf_client import LtzfClient
from bawue_scraper.config import Config


@pytest.mark.integration
class TestLtzfIntegration:
    def test_submit_vorgang_to_local_backend(self, sample_vorgang):
        config = Config()
        client = LtzfClient(config)
        result = client.submit_vorgang(sample_vorgang)
        assert result is True

    def test_submit_vorgang_idempotent(self, sample_vorgang):
        config = Config()
        client = LtzfClient(config)
        first = client.submit_vorgang(sample_vorgang)
        second = client.submit_vorgang(sample_vorgang)
        assert first is True
        assert second is True
