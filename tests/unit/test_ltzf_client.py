"""Tests for the LTZF API client."""

import logging

import pytest
import responses

from bawue_scraper.adapters.ltzf_client import LtzfClient
from bawue_scraper.config import Config

VORGANG_URL = "http://localhost:8080/api/v2/vorgang"


class TestLtzfClientSubmitVorgang:
    @responses.activate
    def test_submit_vorgang_success(self, config, sample_vorgang):
        responses.put(
            "http://localhost:8080/api/v2/vorgang",
            status=201,
        )
        client = LtzfClient(config)
        result = client.submit_vorgang(sample_vorgang)
        assert result is True

    @responses.activate
    def test_submit_vorgang_sends_correct_headers(self, config, sample_vorgang):
        responses.put(
            "http://localhost:8080/api/v2/vorgang",
            status=201,
        )
        client = LtzfClient(config)
        client.submit_vorgang(sample_vorgang)

        request = responses.calls[0].request
        assert request.headers["X-API-Key"] == "test-api-key"
        assert request.headers["X-Scraper-Id"] == "test-collector"
        assert request.headers["Content-Type"] == "application/json"

    @responses.activate
    def test_submit_vorgang_serializes_body(self, config, sample_vorgang):
        responses.put(
            "http://localhost:8080/api/v2/vorgang",
            status=201,
        )
        client = LtzfClient(config)
        client.submit_vorgang(sample_vorgang)

        import json

        request = responses.calls[0].request
        sent_body = json.loads(request.body)
        expected_body = sample_vorgang.model_dump(mode="json", exclude_none=True)
        assert sent_body == expected_body

    @responses.activate
    @pytest.mark.parametrize("status_code", [400, 403, 500])
    def test_submit_vorgang_error_status_returns_false(self, config, sample_vorgang, status_code):
        responses.put(VORGANG_URL, status=status_code)
        client = LtzfClient(config)
        result = client.submit_vorgang(sample_vorgang)
        assert result is False

    @responses.activate
    def test_submit_vorgang_conflict_returns_true(self, config, sample_vorgang):
        responses.put(VORGANG_URL, status=409)
        client = LtzfClient(config)
        result = client.submit_vorgang(sample_vorgang)
        assert result is True

    def test_submit_vorgang_connection_error_logs_concise_message(self, config, sample_vorgang, caplog):
        """ConnectionError should produce a short log message, not a full traceback."""
        client = LtzfClient(config)

        import requests as req

        client._session.put = lambda *a, **kw: (_ for _ in ()).throw(req.ConnectionError("Connection refused"))

        with caplog.at_level(logging.ERROR):
            result = client.submit_vorgang(sample_vorgang)

        assert result is False
        assert "Connection refused" in caplog.text
        # Should NOT contain a full traceback
        assert "Traceback" not in caplog.text


class TestLtzfClientRedirectPolicy:
    def test_redirects_disabled_by_default(self, config):
        """Default config should set max_redirects=0 to prevent API key leakage."""
        client = LtzfClient(config)
        assert client._session.max_redirects == 0

    def test_redirects_enabled_when_configured(self, config, monkeypatch):
        """When ltzf_allow_redirects=True, session keeps default max_redirects."""
        monkeypatch.setenv("LTZF_ALLOW_REDIRECTS", "true")
        cfg = Config()
        client = LtzfClient(cfg)
        assert client._session.max_redirects > 0

    @responses.activate
    def test_redirect_response_returns_false(self, config, sample_vorgang, caplog):
        """A redirect response should result in a TooManyRedirects error and return False."""
        responses.put(
            "http://localhost:8080/api/v2/vorgang",
            status=301,
            headers={"Location": "http://evil.example.com/api/v2/vorgang"},
        )
        client = LtzfClient(config)

        with caplog.at_level(logging.ERROR):
            result = client.submit_vorgang(sample_vorgang)

        assert result is False


class TestLtzfClientSubmitSitzungen:
    def test_submit_sitzungen_not_implemented(self, config, sample_sitzung):
        from datetime import date

        client = LtzfClient(config)
        with pytest.raises(NotImplementedError):
            client.submit_sitzungen(date(2026, 2, 5), [sample_sitzung])


class TestLoggingLtzfClient:
    def test_submit_vorgang_returns_true(self, sample_vorgang, caplog):
        from bawue_scraper.adapters.logging_ltzf_client import LoggingLtzfClient

        client = LoggingLtzfClient()

        with caplog.at_level(logging.INFO):
            result = client.submit_vorgang(sample_vorgang)

        assert result is True
        assert sample_vorgang.titel in caplog.text
        assert "dry-run" in caplog.text.lower() or "DRY-RUN" in caplog.text

    def test_submit_sitzungen_returns_true(self, sample_sitzung, caplog):
        from datetime import date

        from bawue_scraper.adapters.logging_ltzf_client import LoggingLtzfClient

        client = LoggingLtzfClient()

        with caplog.at_level(logging.INFO):
            result = client.submit_sitzungen(date(2026, 2, 5), [sample_sitzung])

        assert result is True
        assert "dry-run" in caplog.text.lower() or "DRY-RUN" in caplog.text
