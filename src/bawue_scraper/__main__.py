"""CLI entrypoint for the BaWue Scraper."""

import argparse
import logging
import sys

from pydantic import ValidationError

from bawue_scraper.adapters.cache_manager import CacheManager
from bawue_scraper.adapters.ics_adapter import IcsAdapter
from bawue_scraper.adapters.ltzf_client import LtzfClient
from bawue_scraper.adapters.parlis_adapter import ParlisAdapter
from bawue_scraper.adapters.pdf_extractor import PdfExtractor
from bawue_scraper.config import Config
from bawue_scraper.orchestrator import Orchestrator


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

    try:
        config = Config()  # type: ignore[call-arg]
    except ValidationError:
        print(
            "Error: Missing required configuration.\n"
            "Set LTZF_API_URL, LTZF_API_KEY, and COLLECTOR_ID as environment variables\n"
            "or create a .env file (see .env.example).",
            file=sys.stderr,
        )
        sys.exit(1)

    log_level = args.log_level or config.log_level
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Wire up adapters
    parlis = ParlisAdapter(config)
    pdf_extractor = PdfExtractor(config)
    ics = IcsAdapter(config)
    ltzf = LtzfClient(config)
    cache = CacheManager(config)

    orchestrator = Orchestrator(
        config=config,
        vorgang_source=parlis,
        document_extractor=pdf_extractor,
        calendar_source=ics,
        ltzf_api=ltzf,
        cache=cache,
    )

    # todo: pass args.vorgangstyp, args.date_from, args.date_to to orchestrator

    if args.kalender_only:
        orchestrator.run_kalender()
    elif args.vorgaenge_only:
        orchestrator.run_vorgaenge()
    else:
        orchestrator.run()


if __name__ == "__main__":
    main()
