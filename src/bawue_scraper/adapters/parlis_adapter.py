"""PARLIS adapter: fetches Vorgang data from the BaWue parliament's PARLIS system."""

import calendar
import logging
import re
import time
from datetime import date

import requests
from lxml import html

from bawue_scraper.config import Config
from bawue_scraper.ports.vorgang_source import RawVorgang, VorgangSource

logger = logging.getLogger(__name__)

BASE_URL = "https://parlis.landtag-bw.de/parlis/"
BROWSE_URL = BASE_URL + "browse.tt.json"
REPORT_URL = BASE_URL + "report.tt.html"
CHUNKSIZE = 50


class ParlisAdapter(VorgangSource):
    """Implements VorgangSource by scraping the PARLIS API."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "LTZF-BaWue-Scraper/0.1",
                "Accept-Language": "de-DE,de;q=0.9",
            }
        )

    def _establish_session(self) -> None:
        """Load the PARLIS main page to establish session cookies."""
        logger.info("Establishing PARLIS session...")
        resp = self._session.get(BASE_URL, timeout=30)
        resp.raise_for_status()
        logger.info("Session established.")

    def _build_query(self, vorgangstyp: str, date_from: date, date_to: date) -> dict:
        return {
            "action": "SearchAndDisplay",
            "report": {
                "rhl": "main",
                "rhlmode": "add",
                "format": "suchergebnis-vorgang-full",
                "mime": "html",
                "sort": "SORT01/D SORT02/D SORT03",
            },
            "search": {
                "lines": {
                    "l1": str(self._config.wahlperiode),
                    "l2": date_from.strftime("%d.%m.%Y"),
                    "l3": date_to.strftime("%d.%m.%Y"),
                    "l4": vorgangstyp,
                },
                "serverrecordname": "vorgang",
            },
            "sources": ["Star"],
        }

    def _fetch_page(self, report_id: str, start: int) -> str:
        params = {
            "report_id": report_id,
            "start": start,
            "chunksize": CHUNKSIZE,
        }
        resp = self._session.get(REPORT_URL, params=params, timeout=30)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_fundstelle_text(text: str) -> dict:
        """Parse a Fundstelle text entry into structured station data."""
        result: dict = {"raw": text}

        date_match = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
        if date_match:
            result["datum"] = date_match.group(1)

        ds_match = re.search(r"Drucksache\s+(\d+/\d+)", text)
        if ds_match:
            result["drucksache"] = ds_match.group(1)

        pp_match = re.search(r"Plenarprotokoll\s+(\d+/\d+)", text)
        if pp_match:
            result["plenarprotokoll"] = pp_match.group(1)

        type_match = re.match(r"^([\w\s\-äöüÄÖÜß]+?)(?:\s{2,}|\t)", text)
        if type_match:
            result["station_typ"] = type_match.group(1).strip()

        ausschuss_match = re.search(
            r"(Ausschuss\s+(?:für|fuer|f\u00c3\u00bcr)\s+[^0-9]+?)(?:\s+\d{2}\.\d{2}\.|\s+Drucksache)",
            text,
        )
        if ausschuss_match:
            result["ausschuss"] = ausschuss_match.group(1).strip()

        pages_match = re.search(r"\((\d+)\s+S\.\)", text)
        if pages_match:
            result["seiten"] = int(pages_match.group(1))

        return result

    @staticmethod
    def _parse_results(html_content: str) -> list[RawVorgang]:
        """Parse Vorgang results from PARLIS HTML response."""
        tree = html.fromstring(html_content)
        records = tree.xpath('.//div[contains(@class, "efxRecordRepeater")]')

        results = []
        for record in records:
            item: dict = {}

            title_links = record.xpath('.//a[@class="efxZoomShort-Vorgang"]')
            if title_links:
                item["titel"] = title_links[0].text_content().strip()

            dts = record.xpath(".//dl/dt")
            for dt in dts:
                label = dt.text_content().strip().rstrip(":")
                if label == "Vorgangs-ID":
                    label = "vorgangs_id"
                dd = dt.getnext()
                if dd is not None:
                    item[label] = dd.text_content().strip()

            fund_links = record.xpath('.//a[@class="fundstellenLinks"]')
            if fund_links:
                item["fundstellen_parsed"] = []
                for link in fund_links:
                    text = link.text_content().strip()
                    href = link.get("href", "")
                    parsed = ParlisAdapter._parse_fundstelle_text(text)
                    parsed["pdf_url"] = href
                    item["fundstellen_parsed"].append(parsed)

            scripts = record.xpath(".//script")
            for script in scripts:
                script_text = script.text_content()
                vid_match = re.search(r"link-(V-\d+)", script_text)
                if vid_match and "vorgangs_id" not in item:
                    item["vorgangs_id"] = vid_match.group(1)

            url_match = None
            for script in scripts:
                url_match = re.search(r'"/parlis/vorgang/(V-\d+)"', script.text_content())
                if url_match:
                    break
            if url_match:
                item["detail_url"] = f"https://parlis.landtag-bw.de/parlis/vorgang/{url_match.group(1)}"

            if item:
                results.append(item)

        return results

    @staticmethod
    def _monthly_windows(date_from: date, date_to: date) -> list[tuple[date, date]]:
        """Split a date range into monthly windows."""
        windows = []
        current = date_from
        while current <= date_to:
            last_day = calendar.monthrange(current.year, current.month)[1]
            window_end = date(current.year, current.month, last_day)
            if window_end > date_to:
                window_end = date_to
            windows.append((current, window_end))
            # Move to first day of next month
            current = date(current.year + 1, 1, 1) if current.month == 12 else date(current.year, current.month + 1, 1)
        return windows

    def _search_single(self, vorgangstyp: str, date_from: date, date_to: date) -> list[RawVorgang] | None:
        """Execute a single search against PARLIS.

        Returns:
            A list of results, or None if the search was too large (status=running).
        """
        query = self._build_query(vorgangstyp, date_from, date_to)
        logger.info(
            "Searching PARLIS: WP=%s, type=%s, dates=%s-%s",
            self._config.wahlperiode,
            vorgangstyp,
            date_from,
            date_to,
        )

        resp = self._session.post(
            BROWSE_URL,
            json=query,
            headers={"Content-Type": "application/json", "Referer": BASE_URL},
            timeout=30,
        )
        resp.raise_for_status()

        data = resp.json()
        report_id = data.get("report_id", "")
        item_count = int(data.get("item_count", 0) or 0)

        if not report_id:
            sources = data.get("sources", {})
            star = sources.get("Star", {})
            if star.get("status") == "running" and int(star.get("hits", 0)) > 0:
                logger.warning(
                    "Search too large (%d hits, still running). Subdividing into monthly windows.",
                    int(star["hits"]),
                )
                return None
            return []

        if item_count == 0:
            return []

        all_results: list[RawVorgang] = []
        for start in range(0, item_count, CHUNKSIZE):
            if start > 0:
                time.sleep(self._config.parlis_request_delay_s)
            html_content = self._fetch_page(report_id, start)
            page_results = self._parse_results(html_content)
            all_results.extend(page_results)
            logger.info("Fetched page start=%d, got %d records", start, len(page_results))

        return all_results

    def search(self, vorgangstyp: str, date_from: date, date_to: date) -> list[RawVorgang]:
        """Search PARLIS for Vorgänge matching the given criteria.

        If PARLIS indicates the result set is too large (status=running), automatically
        subdivides the date range into monthly windows and retries.
        """
        self._establish_session()
        results = self._search_single(vorgangstyp, date_from, date_to)
        if results is not None:
            return results

        # Subdivide into monthly windows
        all_results: list[RawVorgang] = []
        for window_from, window_to in self._monthly_windows(date_from, date_to):
            time.sleep(self._config.parlis_request_delay_s)
            window_results = self._search_single(vorgangstyp, window_from, window_to)
            if window_results is None:
                logger.warning(
                    "Monthly window %s-%s still too large, skipping.",
                    window_from,
                    window_to,
                )
                continue
            all_results.extend(window_results)

        return all_results

    def get_detail(self, vorgang_id: str) -> RawVorgang:
        """Fetch detailed data for a single Vorgang from PARLIS."""
        raise NotImplementedError("Detail pages are SPA-routed; not implemented yet.")
