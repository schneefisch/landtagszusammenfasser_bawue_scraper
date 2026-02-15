"""Tests for the pipeline orchestrator."""

import pytest

from bawue_scraper.orchestrator import Orchestrator


class TestOrchestrator:
    def test_instantiation(
        self,
        config,
        mock_vorgang_source,
        mock_document_extractor,
        mock_calendar_source,
        mock_ltzf_api,
        mock_cache,
    ):
        orch = Orchestrator(
            config=config,
            vorgang_source=mock_vorgang_source,
            document_extractor=mock_document_extractor,
            calendar_source=mock_calendar_source,
            ltzf_api=mock_ltzf_api,
            cache=mock_cache,
        )
        assert orch._config is config
        assert orch._vorgang_source is mock_vorgang_source

    def test_run_not_implemented(
        self,
        config,
        mock_vorgang_source,
        mock_document_extractor,
        mock_calendar_source,
        mock_ltzf_api,
        mock_cache,
    ):
        orch = Orchestrator(
            config=config,
            vorgang_source=mock_vorgang_source,
            document_extractor=mock_document_extractor,
            calendar_source=mock_calendar_source,
            ltzf_api=mock_ltzf_api,
            cache=mock_cache,
        )
        with pytest.raises(NotImplementedError):
            orch.run()

    # todo: add tests for scraping cycle coordination
    # todo: add tests for per-Vorgang error handling
    # todo: add tests for cache interaction (skip processed, mark new)
    # todo: add tests for calendar pipeline
