"""Tests for CLI argument wiring in __main__.py."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from bawue_scraper.__main__ import main


@pytest.fixture()
def wired_main():
    """Patch all adapter classes for main() testing."""
    with (
        patch("bawue_scraper.__main__.Config") as mock_config_cls,
        patch("bawue_scraper.__main__.ParlisAdapter"),
        patch("bawue_scraper.__main__.PdfExtractor"),
        patch("bawue_scraper.__main__.IcsAdapter"),
        patch("bawue_scraper.__main__.LtzfClient") as mock_ltzf,
        patch("bawue_scraper.__main__.LoggingLtzfClient") as mock_logging_ltzf,
        patch("bawue_scraper.__main__.CacheManager"),
        patch("bawue_scraper.__main__.Orchestrator") as mock_orch_cls,
    ):
        mock_config_cls.return_value = MagicMock(log_level="INFO", ltzf_mode="dry-run", scrape_lookback_days=7)
        mock_orch_cls.return_value = MagicMock()
        yield {
            "config_cls": mock_config_cls,
            "orch_cls": mock_orch_cls,
            "orch": mock_orch_cls.return_value,
            "ltzf": mock_ltzf,
            "logging_ltzf": mock_logging_ltzf,
        }


class TestMainWiresArgs:
    def test_type_arg_passed_to_run(self, wired_main):
        main(["--type", "Kleine Anfrage"])

        wired_main["orch"].run.assert_called_once()
        call_kwargs = wired_main["orch"].run.call_args[1]
        assert call_kwargs["vorgangstypen"] == ["Kleine Anfrage"]

    def test_date_args_passed_to_run(self, wired_main):
        main(["--date-from", "01.06.2025", "--date-to", "31.12.2025"])

        wired_main["orch"].run.assert_called_once()
        call_kwargs = wired_main["orch"].run.call_args[1]
        assert call_kwargs["date_from"] == date(2025, 6, 1)
        assert call_kwargs["date_to"] == date(2025, 12, 31)

    def test_no_args_calls_run_without_overrides(self, wired_main):
        main([])

        wired_main["orch"].run.assert_called_once_with()

    def test_vorgaenge_only_with_type_passes_args(self, wired_main):
        main(["--vorgaenge-only", "--type", "Antrag"])

        wired_main["orch"].run_vorgaenge.assert_called_once()
        call_kwargs = wired_main["orch"].run_vorgaenge.call_args[1]
        assert call_kwargs["vorgangstypen"] == ["Antrag"]


class TestLtzfModeWiring:
    def test_dry_run_mode_uses_logging_client(self, wired_main):
        main([])

        wired_main["logging_ltzf"].assert_called_once()
        wired_main["ltzf"].assert_not_called()

    def test_live_mode_uses_real_client(self, wired_main):
        wired_main["config_cls"].return_value = MagicMock(log_level="INFO", ltzf_mode="live")
        main([])

        wired_main["ltzf"].assert_called_once()
        wired_main["logging_ltzf"].assert_not_called()
