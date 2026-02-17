"""CLI entrypoint for the BaWue Scraper."""

import argparse
import logging
from datetime import date, datetime

from bawue_scraper.adapters.cache_manager import CacheManager
from bawue_scraper.adapters.ics_adapter import IcsAdapter
from bawue_scraper.adapters.logging_ltzf_client import LoggingLtzfClient
from bawue_scraper.adapters.ltzf_client import LtzfClient
from bawue_scraper.adapters.parlis_adapter import ParlisAdapter
from bawue_scraper.adapters.pdf_extractor import PdfExtractor
from bawue_scraper.config import Config
from bawue_scraper.orchestrator import DEFAULT_VORGANGSTYPEN, Orchestrator


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="bawue-scraper",
        description="Collector for Baden-Württemberg parliamentary data (PARLIS → LTZF)",
    )
    parser.add_argument(
        "--type",
        dest="vorgangstyp",
        help="Scrape only this Vorgangstyp (e.g. 'Gesetzgebung', 'Kleine Anfrage')",
    )
    parser.add_argument(
        "--date-from",
        help="Start date for scraping range (DD.MM.YYYY)",
    )
    parser.add_argument(
        "--date-to",
        help="End date for scraping range (DD.MM.YYYY)",
    )
    parser.add_argument(
        "--kalender-only",
        action="store_true",
        help="Only scrape and submit calendar/session data",
    )
    parser.add_argument(
        "--vorgaenge-only",
        action="store_true",
        help="Only scrape and submit Vorgänge (skip calendar)",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override the log level from config",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    config = Config()  # type: ignore[call-arg]

    log_level = args.log_level or config.log_level
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Wire up adapters
    parlis = ParlisAdapter(config)
    pdf_extractor = PdfExtractor(config)
    ics = IcsAdapter(config)
    cache = CacheManager(config)

    if config.ltzf_mode == "live":
        ltzf = LtzfClient(config)
        logging.getLogger(__name__).info("LTZF mode: live (submitting to %s)", config.ltzf_api_url)
    else:
        ltzf = LoggingLtzfClient()
        logging.getLogger(__name__).info("LTZF mode: dry-run (logging only, set LTZF_MODE=live to submit)")

    orchestrator = Orchestrator(
        config=config,
        vorgang_source=parlis,
        document_extractor=pdf_extractor,
        calendar_source=ics,
        ltzf_api=ltzf,
        cache=cache,
    )

    # Build override kwargs from CLI args
    overrides: dict = {}
    if args.vorgangstyp:
        overrides["vorgangstypen"] = [args.vorgangstyp]
    if args.date_from:
        overrides["date_from"] = datetime.strptime(args.date_from, "%d.%m.%Y").date()
    if args.date_to:
        overrides["date_to"] = datetime.strptime(args.date_to, "%d.%m.%Y").date()

    if args.kalender_only:
        orchestrator.run_kalender()
    elif args.vorgaenge_only:
        orchestrator.run_vorgaenge(
            vorgangstypen=overrides.get("vorgangstypen", DEFAULT_VORGANGSTYPEN),
            date_from=overrides.get("date_from", date(2026, 1, 1)),
            date_to=overrides.get("date_to", date.today()),
        )
    else:
        orchestrator.run(**overrides)


if __name__ == "__main__":
    main()
