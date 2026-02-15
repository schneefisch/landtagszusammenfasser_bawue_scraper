"""PDF extractor: downloads and extracts text from parliamentary documents."""

from bawue_scraper.config import Config
from bawue_scraper.ports.document_extractor import DocumentExtractor, ExtractionResult


class PdfExtractor(DocumentExtractor):
    """Implements DocumentExtractor using pdfplumber with OCR and LLM fallbacks."""

    def __init__(self, config: Config) -> None:
        self._config = config

    def extract_text(self, url: str) -> ExtractionResult:
        """Download a PDF and extract its text content.

        Extraction waterfall:
        1. pdfplumber (fast, no external deps)
        2. pytesseract OCR (for scanned documents)
        3. OpenAI API (optional, for difficult documents)
        """
        # todo: download PDF from url
        # todo: compute SHA-256 hash of PDF binary
        # todo: try pdfplumber extraction
        # todo: if text too short, try OCR via pytesseract
        # todo: if still insufficient and openai_api_key configured, try LLM extraction
        raise NotImplementedError
