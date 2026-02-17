"""Tests for domain models."""

from bawue_scraper.domain.models import Vorgang


class TestVorgang:
    def test_serialization_roundtrip(self, sample_vorgang):
        data = sample_vorgang.model_dump(mode="json")
        restored = Vorgang.model_validate(data)
        assert restored.titel == sample_vorgang.titel
