"""Port: source of legislative proceedings (Vorgänge)."""

from abc import ABC, abstractmethod
from datetime import date
from typing import TypedDict


class RawFundstelle(TypedDict, total=False):
    """Structured data parsed from a PARLIS Fundstelle text entry."""

    raw: str
    datum: str
    drucksache: str | None
    plenarprotokoll: str | None
    station_typ: str
    ausschuss: str | None
    seiten: int | None
    pdf_url: str | None


class RawVorgang(TypedDict, total=False):
    """Raw Vorgang data as returned by the PARLIS HTML parser.

    Contains both fixed keys (titel, vorgangs_id, etc.) and dynamic keys
    parsed from PARLIS ``<dt>/<dd>`` elements (Vorgangstyp, Initiative, ...).
    """

    titel: str
    vorgangs_id: str
    detail_url: str
    fundstellen_parsed: list[RawFundstelle]
    # Dynamic PARLIS keys (from <dt>/<dd> parsing):
    Vorgangstyp: str
    Initiative: str


class VorgangSource(ABC):
    """Fetches raw Vorgang data from a parliamentary data source."""

    @abstractmethod
    def search(self, vorgangstyp: str, date_from: date, date_to: date) -> list[RawVorgang]:
        """Search for Vorgänge matching the given criteria.

        Args:
            vorgangstyp: The PARLIS Vorgangstyp to search for.
            date_from: Start of the date range.
            date_to: End of the date range.

        Returns:
            A list of raw Vorgang dictionaries.
        """

    @abstractmethod
    def get_detail(self, vorgang_id: str) -> RawVorgang:
        """Fetch detailed data for a single Vorgang.

        Args:
            vorgang_id: The identifier of the Vorgang.

        Returns:
            A dictionary with detailed Vorgang data.
        """
