"""Tests for configuration loading."""

from bawue_scraper.config import Config


class TestConfig:
    def test_loads_from_env(self, config):
        assert config.ltzf_api_url == "http://localhost:8080"
        assert config.ltzf_api_key == "test-api-key"
        assert config.collector_id == "test-collector"

    def test_defaults(self, config):
        assert config.scrape_interval_hours == 24
        assert config.parlis_request_delay_s == 1.0
        assert config.log_level == "INFO"
        assert config.cache_dir == "./cache"
        assert config.wahlperiode == 17
        assert config.openai_api_key is None

    def test_ltzf_mode_defaults_to_dry_run(self, config):
        assert config.ltzf_mode == "dry-run"

    def test_ltzf_mode_from_env(self, monkeypatch):
        monkeypatch.setenv("LTZF_API_URL", "http://localhost:8080")
        monkeypatch.setenv("LTZF_API_KEY", "test-api-key")
        monkeypatch.setenv("COLLECTOR_ID", "test-collector")
        monkeypatch.setenv("LTZF_MODE", "live")
        cfg = Config()
        assert cfg.ltzf_mode == "live"

    def test_custom_values(self, monkeypatch):
        monkeypatch.setenv("LTZF_API_URL", "https://api.example.com")
        monkeypatch.setenv("LTZF_API_KEY", "key-123")
        monkeypatch.setenv("COLLECTOR_ID", "bw-collector")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("CACHE_DIR", "/tmp/cache")
        cfg = Config()
        assert cfg.log_level == "DEBUG"
        assert cfg.cache_dir == "/tmp/cache"
