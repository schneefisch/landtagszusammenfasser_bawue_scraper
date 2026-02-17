"""Pipeline orchestrator: coordinates the scraping workflow via ports."""

import logging
from datetime import date, datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

from bawue_scraper.config import Config
from bawue_scraper.domain.enums import Stationstyp
from bawue_scraper.domain.models import Autor, Dokument, Gremium, Station, Vorgang
from bawue_scraper.mapping.enum_mapper import map_dokumententyp, map_stationstyp, map_vorgangstyp
from bawue_scraper.ports.cache import Cache
from bawue_scraper.ports.calendar_source import CalendarSource
from bawue_scraper.ports.document_extractor import DocumentExtractor
from bawue_scraper.ports.ltzf_api import LtzfApi
from bawue_scraper.ports.vorgang_source import VorgangSource

logger = logging.getLogger(__name__)

# Default Vorgangstypen to scrape — all types available in PARLIS
DEFAULT_VORGANGSTYPEN = [
    "Gesetzgebung",
    "Haushaltsgesetzgebung",
    "Volksantrag",
    "Antrag",
    "Antrag der Landesregierung/eines Ministeriums",
    "Antrag des Rechnungshofs",
    "Kleine Anfrage",
    "Große Anfrage",
    "Mündliche Anfrage",
    "Aktuelle Debatte",
    "Anmerkung zur Plenarsitzung",
    "Ansprache/Erklärung/Mitteilung",
    "Bericht des Parlamentarischen Kontrollgremiums",
    "Besetzung externer Gremien",
    "Besetzung interner Gremien",
    "Enquetekommission",
    "EU-Vorlage",
    "Geschäftsordnung",
    "Immunitätsangelegenheit",
    "Mitteilung der Landesregierung/eines Ministeriums",
    "Mitteilung des Bürgerbeauftragten",
    "Mitteilung des Landesbeauftragten für den Datenschutz",
    "Mitteilung des Präsidenten",
    "Mitteilung des Rechnungshofs",
    "Petitionen",
    "Regierungsbefragung",
    "Regierungserklärung/Regierungsinformation",
    "Schreiben des Bundesverfassungsgerichts",
    "Schreiben des Verfassungsgerichtshofs",
    "Untersuchungsausschuss",
    "Wahl im Landtag",
    "Wahlprüfung",
]


class Orchestrator:
    """Coordinates the scraping pipeline using injected port implementations."""

    def __init__(
        self,
        config: Config,
        vorgang_source: VorgangSource,
        document_extractor: DocumentExtractor,
        calendar_source: CalendarSource,
        ltzf_api: LtzfApi,
        cache: Cache,
    ) -> None:
        self._config = config
        self._vorgang_source = vorgang_source
        self._document_extractor = document_extractor
        self._calendar_source = calendar_source
        self._ltzf_api = ltzf_api
        self._cache = cache

    def run(
        self,
        *,
        vorgangstypen: list[str] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> None:
        """Execute a full scraping cycle.

        Args:
            vorgangstypen: Override the default list of Vorgangstypen to scrape.
            date_from: Override the default start date.
            date_to: Override the default end date.
        """
        self.run_vorgaenge(
            vorgangstypen=vorgangstypen or DEFAULT_VORGANGSTYPEN,
            date_from=date_from or date.today() - timedelta(days=self._config.scrape_lookback_days),
            date_to=date_to or date.today(),
        )
        try:
            self.run_kalender()
        except NotImplementedError:
            logger.info("Calendar pipeline not yet implemented, skipping.")

    def run_vorgaenge(
        self,
        vorgangstypen: list[str],
        date_from: date,
        date_to: date,
    ) -> None:
        """Scrape and submit Vorgänge only."""
        total = 0
        skipped = 0
        submitted = 0
        errors = 0

        for vorgangstyp in vorgangstypen:
            raw_vorgaenge = self._vorgang_source.search(vorgangstyp, date_from, date_to)
            logger.info("Found %d Vorgänge for type '%s'", len(raw_vorgaenge), vorgangstyp)

            for raw in raw_vorgaenge:
                total += 1
                vorgang_id = raw.get("Vorgangs-ID", "unknown")

                if self._cache.is_processed(vorgang_id):
                    skipped += 1
                    logger.debug("Skipping already-processed Vorgang %s", vorgang_id)
                    continue

                try:
                    vorgang = self._build_vorgang(raw)
                    success = self._ltzf_api.submit_vorgang(vorgang)
                    if success:
                        self._cache.mark_processed(vorgang_id)
                        submitted += 1
                    else:
                        errors += 1
                        logger.warning("Failed to submit Vorgang %s", vorgang_id)
                except Exception:
                    errors += 1
                    logger.error("Error processing Vorgang %s", vorgang_id, exc_info=True)

        logger.info(
            "Vorgänge pipeline complete: total=%d, submitted=%d, skipped=%d, errors=%d",
            total,
            submitted,
            skipped,
            errors,
        )

    def run_kalender(self) -> None:
        """Scrape and submit calendar/session data only."""
        raise NotImplementedError("Calendar pipeline not yet implemented.")

    def _build_vorgang(self, raw: dict) -> Vorgang:
        """Convert a raw PARLIS dict into a domain Vorgang model."""
        vorgang_id = raw.get("Vorgangs-ID", "unknown")
        titel = raw.get("titel", "")
        initiative = raw.get("Initiative", "")
        vorgangstyp_str = raw.get("Vorgangstyp", "")

        api_id = uuid5(NAMESPACE_URL, vorgang_id)
        typ = map_vorgangstyp(vorgangstyp_str)
        initiatoren = [Autor(organisation=initiative)] if initiative else []

        stationen = []
        for fund in raw.get("fundstellen_parsed", []):
            station = self._build_station(fund, initiative)
            stationen.append(station)

        return Vorgang(
            api_id=api_id,
            titel=titel,
            typ=typ,
            wahlperiode=self._config.wahlperiode,
            verfassungsaendernd=False,
            initiatoren=initiatoren,
            stationen=stationen,
            ids=[vorgang_id],
        )

    def _build_station(self, fund: dict, initiative: str) -> Station:
        """Convert a parsed Fundstelle dict into a domain Station."""
        station_typ_str = fund.get("station_typ", "")
        station_typ = map_stationstyp(station_typ_str, initiator=initiative)

        # Parse date
        datum_str = fund.get("datum", "")
        zp_start = datetime.strptime(datum_str, "%d.%m.%Y") if datum_str else datetime.now()

        # Determine gremium
        ausschuss = fund.get("ausschuss", "")
        if ausschuss:
            gremium = Gremium(name=ausschuss, wahlperiode=self._config.wahlperiode)
        elif fund.get("plenarprotokoll"):
            gremium = Gremium(name="Plenum", wahlperiode=self._config.wahlperiode)
        else:
            gremium = Gremium(name="Landtag", wahlperiode=self._config.wahlperiode)

        # Build document
        dokumente = []
        pdf_url = fund.get("pdf_url", "")
        if pdf_url:
            doc_typ = map_dokumententyp(
                station_typ_str,
                is_vorparlamentarisch=(station_typ == Stationstyp.PREPARL_REGENT),
            )

            volltext = ""
            doc_hash = ""
            try:
                result = self._document_extractor.extract_text(pdf_url)
                volltext = result.text
                doc_hash = result.hash
            except NotImplementedError:
                logger.debug("Document extractor not implemented, skipping PDF text extraction")
            except Exception:
                logger.warning("Failed to extract text from %s", pdf_url, exc_info=True)

            dokumente.append(
                Dokument(
                    titel=station_typ_str or "Dokument",
                    volltext=volltext,
                    hash=doc_hash,
                    typ=doc_typ,
                    zp_modifiziert=zp_start,
                    zp_referenz=zp_start,
                    link=pdf_url,
                    autoren=[],
                    drucksnr=fund.get("drucksache"),
                )
            )

        return Station(
            typ=station_typ,
            dokumente=dokumente,
            zp_start=zp_start,
            gremium=gremium,
        )
