"""Port: document text extraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """Result of a document text extraction."""

    text: str
    hash: str
    page_count: int


class DocumentExtractor(ABC):
    """Extracts text content from document binaries (e.g. PDFs)."""

    @abstractmethod
    def extract_text(self, url: str) -> ExtractionResult:
        """Download a document and extract its text content.

        Args:
            url: The URL of the document to download.

        Returns:
            An ExtractionResult with extracted text, hash, and page count.
        """
