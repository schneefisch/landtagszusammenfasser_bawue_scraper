"""Pydantic domain models mirroring the LTZF API data structures."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl

from bawue_scraper.domain.enums import Dokumententyp, Stationstyp, Vorgangstyp


class Autor(BaseModel):
    """Author / initiator of a Vorgang or Dokument."""

    organisation: str
    person: str | None = None
    fachgebiet: str | None = None
    lobbyregister: str | None = None


class Gremium(BaseModel):
    """Parliamentary committee or plenary body."""

    parlament: str = "BW"
    name: str
    wahlperiode: int = 17


class Dokument(BaseModel):
    """A parliamentary document (Drucksache, Protokoll, etc.)."""

    titel: str
    volltext: str
    hash: str
    typ: Dokumententyp
    zp_modifiziert: datetime
    zp_referenz: datetime
    link: HttpUrl
    autoren: list[Autor]
    drucksnr: str | None = None
    kurztitel: str | None = None
    vorwort: str | None = None
    zusammenfassung: str | None = None
    meinung: int | None = None
    schlagworte: list[str] | None = None


class Station(BaseModel):
    """A stage in the legislative process."""

    typ: Stationstyp
    dokumente: list[Dokument]
    zp_start: datetime
    gremium: Gremium
    titel: str | None = None
    link: HttpUrl | None = None
    schlagworte: list[str] | None = None
    stellungnahmen: list[Dokument] | None = None
    trojanergefahr: int | None = None


class Vorgang(BaseModel):
    """A complete legislative proceeding."""

    api_id: UUID
    titel: str
    typ: Vorgangstyp
    wahlperiode: int = 17
    verfassungsaendernd: bool = False
    initiatoren: list[Autor]
    stationen: list[Station]
    kurztitel: str | None = None
    ids: list[str] | None = None
    links: list[HttpUrl] | None = None
    lobbyregister: list[str] | None = None


class Top(BaseModel):
    """Agenda item (Tagesordnungspunkt) of a parliamentary session."""

    nummer: str
    titel: str
    vorgang_id: UUID | None = None
    dokumente: list[Dokument] | None = None


class Sitzung(BaseModel):
    """A parliamentary session."""

    termin: datetime
    gremium: Gremium
    nummer: int
    tops: list[Top]
    public: bool = True
