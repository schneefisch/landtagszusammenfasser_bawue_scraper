"""Tests for the pipeline orchestrator."""

import logging
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from bawue_scraper.orchestrator import DEFAULT_VORGANGSTYPEN, Orchestrator


@pytest.fixture()
def orchestrator(config, mock_vorgang_source, mock_document_extractor, mock_calendar_source, mock_ltzf_api, mock_cache):
    return Orchestrator(
        config=config,
        vorgang_source=mock_vorgang_source,
        document_extractor=mock_document_extractor,
        calendar_source=mock_calendar_source,
        ltzf_api=mock_ltzf_api,
        cache=mock_cache,
    )


def _make_raw_vorgang(vid: str, titel: str = "Test Gesetz", vorgangstyp: str = "Gesetzgebung") -> dict:
    """Create a minimal raw Vorgang dict as returned by ParlisAdapter."""
    return {
        "titel": titel,
        "vorgangs_id": vid,
        "Vorgangstyp": vorgangstyp,
        "Initiative": "Fraktion GRÜNE",
        "fundstellen_parsed": [
            {
                "raw": "Gesetzentwurf    Fraktion GRÜNE  04.02.2026 Drucksache 17/10266   (13 S.)",
                "datum": "04.02.2026",
                "drucksache": "17/10266",
                "station_typ": "Gesetzentwurf",
                "seiten": 13,
                "pdf_url": "https://www.landtag-bw.de/resource/blob/12345/doc.pdf",
            },
            {
                "raw": "Erste Beratung   Plenarprotokoll 17/141 05.02.2026",
                "datum": "05.02.2026",
                "plenarprotokoll": "17/141",
                "station_typ": "Erste Beratung",
                "pdf_url": "",
            },
        ],
    }


class TestRunVorgaenge:
    def test_happy_path_submits_all(self, orchestrator, mock_vorgang_source, mock_ltzf_api, mock_cache):
        mock_vorgang_source.search.return_value = [
            _make_raw_vorgang("V-001"),
            _make_raw_vorgang("V-002"),
        ]
        mock_cache.is_processed.return_value = False
        mock_ltzf_api.submit_vorgang.return_value = True

        orchestrator.run_vorgaenge(
            vorgangstypen=["Gesetzgebung"],
            date_from=date(2026, 1, 1),
            date_to=date(2026, 2, 1),
        )

        assert mock_ltzf_api.submit_vorgang.call_count == 2
        assert mock_cache.mark_processed.call_count == 2
        mock_cache.mark_processed.assert_any_call("V-001")
        mock_cache.mark_processed.assert_any_call("V-002")

    def test_skips_cached_vorgaenge(self, orchestrator, mock_vorgang_source, mock_ltzf_api, mock_cache):
        mock_vorgang_source.search.return_value = [
            _make_raw_vorgang("V-001"),
            _make_raw_vorgang("V-002"),
        ]
        mock_cache.is_processed.side_effect = lambda vid: vid == "V-001"
        mock_ltzf_api.submit_vorgang.return_value = True

        orchestrator.run_vorgaenge(
            vorgangstypen=["Gesetzgebung"],
            date_from=date(2026, 1, 1),
            date_to=date(2026, 2, 1),
        )

        assert mock_ltzf_api.submit_vorgang.call_count == 1
        mock_cache.mark_processed.assert_called_once_with("V-002")

    def test_continues_on_per_vorgang_error(self, orchestrator, mock_vorgang_source, mock_ltzf_api, mock_cache, caplog):
        mock_vorgang_source.search.return_value = [
            _make_raw_vorgang("V-001"),
            _make_raw_vorgang("V-002"),
        ]
        mock_cache.is_processed.return_value = False
        mock_ltzf_api.submit_vorgang.side_effect = [RuntimeError("API down"), True]

        with caplog.at_level(logging.ERROR):
            orchestrator.run_vorgaenge(
                vorgangstypen=["Gesetzgebung"],
                date_from=date(2026, 1, 1),
                date_to=date(2026, 2, 1),
            )

        assert mock_ltzf_api.submit_vorgang.call_count == 2
        # Only V-002 marked as processed (V-001 errored)
        mock_cache.mark_processed.assert_called_once_with("V-002")
        assert "V-001" in caplog.text

    def test_multiple_vorgangstypen(self, orchestrator, mock_vorgang_source, mock_ltzf_api, mock_cache):
        mock_vorgang_source.search.side_effect = [
            [_make_raw_vorgang("V-001")],
            [_make_raw_vorgang("V-002")],
        ]
        mock_cache.is_processed.return_value = False
        mock_ltzf_api.submit_vorgang.return_value = True

        orchestrator.run_vorgaenge(
            vorgangstypen=["Gesetzgebung", "Kleine Anfrage"],
            date_from=date(2026, 1, 1),
            date_to=date(2026, 2, 1),
        )

        assert mock_vorgang_source.search.call_count == 2
        assert mock_ltzf_api.submit_vorgang.call_count == 2

    def test_empty_search_results(self, orchestrator, mock_vorgang_source, mock_ltzf_api, mock_cache):
        mock_vorgang_source.search.return_value = []

        orchestrator.run_vorgaenge(
            vorgangstypen=["Gesetzgebung"],
            date_from=date(2026, 1, 1),
            date_to=date(2026, 2, 1),
        )

        mock_ltzf_api.submit_vorgang.assert_not_called()
        mock_cache.mark_processed.assert_not_called()

    def test_does_not_mark_processed_when_submit_fails(
        self, orchestrator, mock_vorgang_source, mock_ltzf_api, mock_cache
    ):
        mock_vorgang_source.search.return_value = [
            _make_raw_vorgang("V-001"),
            _make_raw_vorgang("V-002"),
        ]
        mock_cache.is_processed.return_value = False
        mock_ltzf_api.submit_vorgang.side_effect = [False, True]

        orchestrator.run_vorgaenge(
            vorgangstypen=["Gesetzgebung"],
            date_from=date(2026, 1, 1),
            date_to=date(2026, 2, 1),
        )

        # V-001 returned False, should NOT be marked as processed
        mock_cache.mark_processed.assert_called_once_with("V-002")

    def test_failed_submit_counted_as_error(self, orchestrator, mock_vorgang_source, mock_ltzf_api, mock_cache, caplog):
        mock_vorgang_source.search.return_value = [_make_raw_vorgang("V-001")]
        mock_cache.is_processed.return_value = False
        mock_ltzf_api.submit_vorgang.return_value = False

        with caplog.at_level(logging.INFO):
            orchestrator.run_vorgaenge(
                vorgangstypen=["Gesetzgebung"],
                date_from=date(2026, 1, 1),
                date_to=date(2026, 2, 1),
            )

        assert "V-001" in caplog.text
        assert "errors=1" in caplog.text

    def test_statistics_logged(self, orchestrator, mock_vorgang_source, mock_ltzf_api, mock_cache, caplog):
        mock_vorgang_source.search.return_value = [
            _make_raw_vorgang("V-001"),
            _make_raw_vorgang("V-002"),
            _make_raw_vorgang("V-003"),
        ]
        mock_cache.is_processed.side_effect = lambda vid: vid == "V-002"
        mock_ltzf_api.submit_vorgang.return_value = True

        with caplog.at_level(logging.INFO):
            orchestrator.run_vorgaenge(
                vorgangstypen=["Gesetzgebung"],
                date_from=date(2026, 1, 1),
                date_to=date(2026, 2, 1),
            )

        # Check summary logging
        assert "3" in caplog.text  # total
        assert "1" in caplog.text  # skipped
        assert "2" in caplog.text  # submitted


class TestRunKalender:
    def test_raises_not_implemented(self, orchestrator):
        with pytest.raises(NotImplementedError):
            orchestrator.run_kalender()


class TestDefaultVorgangstypen:
    def test_contains_all_parlis_types(self):
        assert "Gesetzgebung" in DEFAULT_VORGANGSTYPEN
        assert "Kleine Anfrage" in DEFAULT_VORGANGSTYPEN
        assert "Antrag" in DEFAULT_VORGANGSTYPEN
        assert "Enquetekommission" in DEFAULT_VORGANGSTYPEN
        assert "Wahlprüfung" in DEFAULT_VORGANGSTYPEN
        assert len(DEFAULT_VORGANGSTYPEN) == 32


class TestRun:
    def test_run_calls_run_vorgaenge(self, orchestrator, mock_vorgang_source, mock_ltzf_api, mock_cache):
        mock_vorgang_source.search.return_value = []
        mock_cache.is_processed.return_value = False

        orchestrator.run()

        # run_vorgaenge should have been called (search was invoked)
        assert mock_vorgang_source.search.call_count > 0

    def test_run_catches_kalender_not_implemented(self, orchestrator, mock_vorgang_source, mock_cache):
        mock_vorgang_source.search.return_value = []
        # Should not raise even though run_kalender raises NotImplementedError
        orchestrator.run()

    def test_run_with_single_type_override(self, orchestrator, mock_vorgang_source, mock_cache):
        mock_vorgang_source.search.return_value = []

        orchestrator.run(vorgangstypen=["Antrag"])

        assert mock_vorgang_source.search.call_count == 1
        call_args = mock_vorgang_source.search.call_args
        assert call_args[0][0] == "Antrag"

    def test_run_with_date_overrides(self, orchestrator, mock_vorgang_source, mock_cache):
        mock_vorgang_source.search.return_value = []

        orchestrator.run(
            vorgangstypen=["Gesetzgebung"],
            date_from=date(2025, 6, 1),
            date_to=date(2025, 12, 31),
        )

        call_args = mock_vorgang_source.search.call_args
        assert call_args[0][1] == date(2025, 6, 1)
        assert call_args[0][2] == date(2025, 12, 31)

    def test_run_defaults_use_all_vorgangstypen(self, orchestrator, mock_vorgang_source, mock_cache):
        mock_vorgang_source.search.return_value = []

        orchestrator.run()

        assert mock_vorgang_source.search.call_count == len(DEFAULT_VORGANGSTYPEN)

    @patch("bawue_scraper.orchestrator.date")
    def test_run_default_date_from_uses_lookback(
        self, mock_date, orchestrator, mock_vorgang_source, mock_cache, config
    ):
        fake_today = date(2026, 2, 17)
        mock_date.today.return_value = fake_today
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
        mock_vorgang_source.search.return_value = []

        orchestrator.run(vorgangstypen=["Gesetzgebung"])

        call_args = mock_vorgang_source.search.call_args
        expected_from = fake_today - timedelta(days=config.scrape_lookback_days)
        assert call_args[0][1] == expected_from
        assert call_args[0][2] == fake_today


class TestBuildVorgang:
    def test_builds_domain_vorgang(self, orchestrator):
        raw = _make_raw_vorgang("V-001", titel="Testgesetz")
        vorgang = orchestrator._build_vorgang(raw)

        assert vorgang.titel == "Testgesetz"
        assert str(vorgang.api_id)  # UUID generated
        assert len(vorgang.stationen) == 2
        assert vorgang.ids == ["V-001"]

    def test_deterministic_api_id(self, orchestrator):
        raw = _make_raw_vorgang("V-001")
        v1 = orchestrator._build_vorgang(raw)
        v2 = orchestrator._build_vorgang(raw)
        assert v1.api_id == v2.api_id

    def test_different_ids_produce_different_api_ids(self, orchestrator):
        v1 = orchestrator._build_vorgang(_make_raw_vorgang("V-001"))
        v2 = orchestrator._build_vorgang(_make_raw_vorgang("V-002"))
        assert v1.api_id != v2.api_id
