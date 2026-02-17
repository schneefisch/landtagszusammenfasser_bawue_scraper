"""Tests for configuration loading."""

import pytest
from pydantic import ValidationError

from bawue_scraper.config import Config


class TestConfig:
    def test_ltzf_mode_defaults_to_dry_run(self, config):
        assert config.ltzf_mode == "dry-run"

    def test_ltzf_mode_rejects_invalid_value(self, monkeypatch):
        monkeypatch.setenv("LTZF_API_URL", "http://localhost:8080")
        monkeypatch.setenv("LTZF_API_KEY", "test-api-key")
        monkeypatch.setenv("COLLECTOR_ID", "test-collector")
        monkeypatch.setenv("LTZF_MODE", "invalid-mode")
        with pytest.raises(ValidationError):
            Config()
