"""Tests for the PDF extractor."""

import pytest

from bawue_scraper.adapters.pdf_extractor import PdfExtractor


class TestPdfExtractor:
    def test_instantiation(self, config):
        extractor = PdfExtractor(config)
        assert extractor._config is config

    def test_extract_text_not_implemented(self, config):
        extractor = PdfExtractor(config)
        with pytest.raises(NotImplementedError):
            extractor.extract_text("https://www.landtag-bw.de/resource/blob/12345/doc.pdf")

    # todo: add tests for pdfplumber extraction with mocked PDF
    # todo: add tests for OCR fallback
    # todo: add tests for LLM fallback
    # todo: add tests for hash computation
