"""Tests for CLI argument wiring in __main__.py."""

from datetime import date
from unittest.mock import MagicMock, patch

from bawue_scraper.__main__ import build_parser, main


class TestBuildParser:
    def test_type_arg(self):
        parser = build_parser()
        args = parser.parse_args(["--type", "Kleine Anfrage"])
        assert args.vorgangstyp == "Kleine Anfrage"

    def test_date_from_arg(self):
        parser = build_parser()
        args = parser.parse_args(["--date-from", "01.06.2025"])
        assert args.date_from == "01.06.2025"

    def test_date_to_arg(self):
        parser = build_parser()
        args = parser.parse_args(["--date-to", "31.12.2025"])
        assert args.date_to == "31.12.2025"

    def test_all_args_combined(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "--type",
                "Antrag",
                "--date-from",
                "01.01.2025",
                "--date-to",
                "31.12.2025",
            ]
        )
        assert args.vorgangstyp == "Antrag"
        assert args.date_from == "01.01.2025"
        assert args.date_to == "31.12.2025"


class TestMainWiresArgs:
    @patch("bawue_scraper.__main__.Orchestrator")
    @patch("bawue_scraper.__main__.CacheManager")
    @patch("bawue_scraper.__main__.LtzfClient")
    @patch("bawue_scraper.__main__.IcsAdapter")
    @patch("bawue_scraper.__main__.PdfExtractor")
    @patch("bawue_scraper.__main__.ParlisAdapter")
    @patch("bawue_scraper.__main__.Config")
    def test_type_arg_passed_to_run(
        self, mock_config_cls, mock_parlis, mock_pdf, mock_ics, mock_ltzf, mock_cache, mock_orch_cls, monkeypatch
    ):
        mock_config_cls.return_value = MagicMock(log_level="INFO", ltzf_mode="dry-run")
        mock_orch = MagicMock()
        mock_orch_cls.return_value = mock_orch

        main(["--type", "Kleine Anfrage"])

        mock_orch.run.assert_called_once()
        call_kwargs = mock_orch.run.call_args[1]
        assert call_kwargs["vorgangstypen"] == ["Kleine Anfrage"]

    @patch("bawue_scraper.__main__.Orchestrator")
    @patch("bawue_scraper.__main__.CacheManager")
    @patch("bawue_scraper.__main__.LtzfClient")
    @patch("bawue_scraper.__main__.IcsAdapter")
    @patch("bawue_scraper.__main__.PdfExtractor")
    @patch("bawue_scraper.__main__.ParlisAdapter")
    @patch("bawue_scraper.__main__.Config")
    def test_date_args_passed_to_run(
        self, mock_config_cls, mock_parlis, mock_pdf, mock_ics, mock_ltzf, mock_cache, mock_orch_cls
    ):
        mock_config_cls.return_value = MagicMock(log_level="INFO", ltzf_mode="dry-run")
        mock_orch = MagicMock()
        mock_orch_cls.return_value = mock_orch

        main(["--date-from", "01.06.2025", "--date-to", "31.12.2025"])

        mock_orch.run.assert_called_once()
        call_kwargs = mock_orch.run.call_args[1]
        assert call_kwargs["date_from"] == date(2025, 6, 1)
        assert call_kwargs["date_to"] == date(2025, 12, 31)

    @patch("bawue_scraper.__main__.Orchestrator")
    @patch("bawue_scraper.__main__.CacheManager")
    @patch("bawue_scraper.__main__.LtzfClient")
    @patch("bawue_scraper.__main__.IcsAdapter")
    @patch("bawue_scraper.__main__.PdfExtractor")
    @patch("bawue_scraper.__main__.ParlisAdapter")
    @patch("bawue_scraper.__main__.Config")
    def test_no_args_calls_run_without_overrides(
        self, mock_config_cls, mock_parlis, mock_pdf, mock_ics, mock_ltzf, mock_cache, mock_orch_cls
    ):
        mock_config_cls.return_value = MagicMock(log_level="INFO", ltzf_mode="dry-run")
        mock_orch = MagicMock()
        mock_orch_cls.return_value = mock_orch

        main([])

        mock_orch.run.assert_called_once_with()

    @patch("bawue_scraper.__main__.Orchestrator")
    @patch("bawue_scraper.__main__.CacheManager")
    @patch("bawue_scraper.__main__.LtzfClient")
    @patch("bawue_scraper.__main__.IcsAdapter")
    @patch("bawue_scraper.__main__.PdfExtractor")
    @patch("bawue_scraper.__main__.ParlisAdapter")
    @patch("bawue_scraper.__main__.Config")
    def test_vorgaenge_only_with_type_passes_args(
        self, mock_config_cls, mock_parlis, mock_pdf, mock_ics, mock_ltzf, mock_cache, mock_orch_cls
    ):
        mock_config_cls.return_value = MagicMock(log_level="INFO", ltzf_mode="dry-run", scrape_lookback_days=7)
        mock_orch = MagicMock()
        mock_orch_cls.return_value = mock_orch

        main(["--vorgaenge-only", "--type", "Antrag"])

        mock_orch.run_vorgaenge.assert_called_once()
        call_kwargs = mock_orch.run_vorgaenge.call_args[1]
        assert call_kwargs["vorgangstypen"] == ["Antrag"]


class TestLtzfModeWiring:
    @patch("bawue_scraper.__main__.Orchestrator")
    @patch("bawue_scraper.__main__.CacheManager")
    @patch("bawue_scraper.__main__.LtzfClient")
    @patch("bawue_scraper.__main__.LoggingLtzfClient")
    @patch("bawue_scraper.__main__.IcsAdapter")
    @patch("bawue_scraper.__main__.PdfExtractor")
    @patch("bawue_scraper.__main__.ParlisAdapter")
    @patch("bawue_scraper.__main__.Config")
    def test_dry_run_mode_uses_logging_client(
        self, mock_config_cls, mock_parlis, mock_pdf, mock_ics, mock_logging_ltzf, mock_ltzf, mock_cache, mock_orch_cls
    ):
        mock_config_cls.return_value = MagicMock(log_level="INFO", ltzf_mode="dry-run")
        mock_orch_cls.return_value = MagicMock()

        main([])

        mock_logging_ltzf.assert_called_once()
        mock_ltzf.assert_not_called()

    @patch("bawue_scraper.__main__.Orchestrator")
    @patch("bawue_scraper.__main__.CacheManager")
    @patch("bawue_scraper.__main__.LtzfClient")
    @patch("bawue_scraper.__main__.LoggingLtzfClient")
    @patch("bawue_scraper.__main__.IcsAdapter")
    @patch("bawue_scraper.__main__.PdfExtractor")
    @patch("bawue_scraper.__main__.ParlisAdapter")
    @patch("bawue_scraper.__main__.Config")
    def test_live_mode_uses_real_client(
        self, mock_config_cls, mock_parlis, mock_pdf, mock_ics, mock_logging_ltzf, mock_ltzf, mock_cache, mock_orch_cls
    ):
        mock_config_cls.return_value = MagicMock(log_level="INFO", ltzf_mode="live")
        mock_orch_cls.return_value = MagicMock()

        main([])

        mock_ltzf.assert_called_once()
        mock_logging_ltzf.assert_not_called()
