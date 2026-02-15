#!/usr/bin/env python3
"""
PARLIS API Test Script

Tests the undocumented PARLIS JSON-API of the Baden-Württemberg state parliament
to evaluate data availability for the LTZF (Landtagszusammenfasser) project.

Tests:
1. Gesetzgebung (legislation) search — extract station data from Fundstellen
2. Vorgang detail page via PARLIS internal search
3. Discover all available Vorgangstyp values
4. Sitzung/TOP data availability (ICS calendar)

Usage:
    python scripts/parlis_test.py

Findings from initial testing:
- Only serverrecordname="vorgang" works; other values stay "running" forever
- Detail pages are SPA-routed, can't be fetched via GET
- Fundstellen in list view contain rich station data (dates, committees, PDFs)
"""

import json
import logging
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from lxml import html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

BASE_URL = "https://parlis.landtag-bw.de/parlis/"
BROWSE_URL = urljoin(BASE_URL, "browse.tt.json")
REPORT_URL = urljoin(BASE_URL, "report.tt.html")
OUTPUT_DIR = Path(__file__).parent / "output"

# Delay between requests to be respectful
REQUEST_DELAY_S = 1.0


def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_session() -> requests.Session:
    """Establish a PARLIS session by loading the main page to get cookies."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "LTZF-BaWue-Scraper-Test/0.1 (research)",
            "Accept-Language": "de-DE,de;q=0.9",
        }
    )

    log.info("Establishing PARLIS session...")
    resp = session.get(BASE_URL, timeout=30)
    resp.raise_for_status()
    log.info(
        "Session established. Cookies: %s",
        {k: v[:20] + "..." for k, v in session.cookies.get_dict().items()},
    )
    return session


def search_parlis(
    session: requests.Session,
    *,
    wahlperiode: str = "17",
    vorgangstyp: str = "",
    start_date: str = "",
    end_date: str = "",
) -> tuple[str, int]:
    """
    Execute a PARLIS Vorgang search and return (report_id, item_count).

    Only serverrecordname="vorgang" with format="suchergebnis-vorgang-full" works.
    Other combinations stay "running" indefinitely.
    """
    query = {
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
                "l1": wahlperiode,
                "l2": start_date,
                "l3": end_date,
                "l4": vorgangstyp,
            },
            "serverrecordname": "vorgang",
        },
        "sources": ["Star"],
    }

    log.info(
        "Searching PARLIS: WP=%s, type=%s, dates=%s–%s",
        wahlperiode,
        vorgangstyp or "(all)",
        start_date or "*",
        end_date or "*",
    )

    resp = session.post(
        BROWSE_URL,
        json=query,
        headers={
            "Content-Type": "application/json",
            "Referer": BASE_URL,
        },
        timeout=30,
    )
    resp.raise_for_status()

    data = resp.json()
    report_id = data.get("report_id", "")
    item_count = int(data.get("item_count", 0) or 0)
    log.info("Search result: report_id=%s, item_count=%d", report_id[:30] + "..." if report_id else "", item_count)

    if not report_id:
        # Check if it's a "too many results" situation (status: running with hits > 0)
        sources = data.get("sources", {})
        star = sources.get("Star", {})
        if star.get("status") == "running" and int(star.get("hits", 0)) > 0:
            total_hits = int(star["hits"])
            log.info(
                "Search too large (%d hits, still running). Use date filters to reduce scope.",
                total_hits,
            )
            return "", total_hits  # Return count but no report_id
        log.warning("No report_id. Response: %s", json.dumps(data, indent=2))

    return report_id, item_count


def fetch_results(
    session: requests.Session,
    report_id: str,
    start: int = 0,
    chunksize: int = 10,
) -> str:
    """Fetch paginated HTML results for a given report_id."""
    params = {
        "report_id": report_id,
        "start": start,
        "chunksize": chunksize,
    }

    log.info("Fetching results: start=%d, chunksize=%d", start, chunksize)
    resp = session.get(REPORT_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_fundstelle_text(text: str) -> dict:
    """
    Parse a Fundstelle text entry into structured station data.

    Examples:
        "Gesetzentwurf    Fraktion GRÜNE, Fraktion der CDU  04.02.2026 Drucksache 17/10266   (13 S.)"
        "Erste Beratung   Plenarprotokoll 17/141 05.02.2026"
        "Beschlussempfehlung und Bericht    Ausschuss für Wirtschaft  02.02.2026 Drucksache 17/10210"
    """
    result = {"raw": text}

    # Extract date (DD.MM.YYYY)
    date_match = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    if date_match:
        result["datum"] = date_match.group(1)

    # Extract Drucksache number
    ds_match = re.search(r"Drucksache\s+(\d+/\d+)", text)
    if ds_match:
        result["drucksache"] = ds_match.group(1)

    # Extract Plenarprotokoll reference
    pp_match = re.search(r"Plenarprotokoll\s+(\d+/\d+)", text)
    if pp_match:
        result["plenarprotokoll"] = pp_match.group(1)

    # Extract station type (first phrase before spaces/tabs)
    type_match = re.match(r"^([\w\s\-äöüÄÖÜß]+?)(?:\s{2,}|\t)", text)
    if type_match:
        result["station_typ"] = type_match.group(1).strip()

    # Extract committee name (Ausschuss für ...)
    # Handle both proper UTF-8 "für" and mojibake "fÃ¼r"
    ausschuss_match = re.search(r"(Ausschuss\s+(?:für|fuer|f\u00c3\u00bcr)\s+[^0-9]+?)(?:\s+\d{2}\.\d{2}\.|\s+Drucksache)", text)
    if ausschuss_match:
        result["ausschuss"] = ausschuss_match.group(1).strip()

    # Extract page count
    pages_match = re.search(r"\((\d+)\s+S\.\)", text)
    if pages_match:
        result["seiten"] = int(pages_match.group(1))

    return result


def parse_vorgang_results(html_content: str) -> list[dict]:
    """Parse Vorgang results from PARLIS HTML response."""
    tree = html.fromstring(html_content)
    records = tree.xpath('.//div[contains(@class, "efxRecordRepeater")]')
    log.info("Found %d records in HTML", len(records))

    results = []
    for record in records:
        item = {}

        # Title (from zoom link, href is empty — set via JS)
        title_links = record.xpath('.//a[@class="efxZoomShort-Vorgang"]')
        if title_links:
            item["titel"] = title_links[0].text_content().strip()

        # Extract all dt/dd pairs from definition lists
        dts = record.xpath(".//dl/dt")
        for dt in dts:
            label = dt.text_content().strip().rstrip(":")
            dd = dt.getnext()
            if dd is not None:
                value = dd.text_content().strip()
                item[label] = value

        # Document links (Fundstellen) — these contain station data!
        fund_links = record.xpath('.//a[@class="fundstellenLinks"]')
        if fund_links:
            item["fundstellen_parsed"] = []
            for link in fund_links:
                text = link.text_content().strip()
                href = link.get("href", "")
                parsed = parse_fundstelle_text(text)
                parsed["pdf_url"] = href
                item["fundstellen_parsed"].append(parsed)

        # Extract Vorgangs-ID from the JS block as fallback
        scripts = record.xpath(".//script")
        for script in scripts:
            script_text = script.text_content()
            vid_match = re.search(r"link-(V-\d+)", script_text)
            if vid_match and "Vorgangs-ID" not in item:
                item["Vorgangs-ID"] = vid_match.group(1)

        # Also extract the detail URL pattern from JS
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


def save_html(filename: str, content: str):
    """Save content to the output directory."""
    path = OUTPUT_DIR / filename
    path.write_text(content, encoding="utf-8")
    log.info("Saved to %s (%d bytes)", path, len(content))


def print_separator(title: str):
    print(f"\n{'#' * 70}")
    print(f"# {title}")
    print(f"{'#' * 70}")


def test_gesetzgebung_search(session: requests.Session) -> list[dict]:
    """Test 1: Search for Gesetzgebung and analyze station data from Fundstellen."""
    print_separator("TEST 1: Gesetzgebung Search — Station Data Analysis")

    report_id, item_count = search_parlis(session, vorgangstyp="Gesetzgebung")
    if not report_id:
        log.error("Test 1 FAILED: No report_id")
        return []

    print(f"\n  Total Gesetzgebung Vorgänge in WP 17: {item_count}")

    time.sleep(REQUEST_DELAY_S)
    html_content = fetch_results(session, report_id, start=0, chunksize=10)
    save_html("gesetzgebung_results.html", html_content)

    results = parse_vorgang_results(html_content)
    print(f"  Parsed {len(results)} results from first page")

    # Analyze fields
    all_fields = set()
    for r in results:
        all_fields.update(k for k in r.keys() if k not in ("fundstellen_parsed",))
    print(f"\n  Fields available per Vorgang: {sorted(all_fields)}")

    # Analyze station types from Fundstellen
    print("\n  --- Station Types Found in Fundstellen ---")
    all_station_types = set()
    all_committees = set()

    for r in results:
        for f in r.get("fundstellen_parsed", []):
            st = f.get("station_typ", "")
            if st:
                all_station_types.add(st)
            committee = f.get("ausschuss", "")
            if committee:
                all_committees.add(committee)

    print(f"\n  Station types ({len(all_station_types)}):")
    for t in sorted(all_station_types):
        print(f"    - {t}")

    print(f"\n  Committees ({len(all_committees)}):")
    for c in sorted(all_committees):
        print(f"    - {c}")

    # Show detailed Fundstellen for one complete Vorgang (one with most stations)
    most_stations = max(results, key=lambda r: len(r.get("fundstellen_parsed", [])))
    print(f"\n  --- Most Complete Vorgang: {most_stations.get('titel', '?')[:70]} ---")
    print(f"  Vorgangs-ID: {most_stations.get('Vorgangs-ID', '?')}")
    print(f"  Aktueller Stand: {most_stations.get('Aktueller Stand', '?')}")
    print(f"  Initiative: {most_stations.get('Initiative', '?')}")
    print(f"  Stations ({len(most_stations.get('fundstellen_parsed', []))}):")
    for i, f in enumerate(most_stations.get("fundstellen_parsed", []), 1):
        print(f"    {i}. {f.get('station_typ', '?')}")
        print(f"       Datum: {f.get('datum', '-')}")
        if f.get("drucksache"):
            print(f"       Drucksache: {f['drucksache']}")
        if f.get("plenarprotokoll"):
            print(f"       Plenarprotokoll: {f['plenarprotokoll']}")
        if f.get("ausschuss"):
            print(f"       Ausschuss: {f['ausschuss']}")
        if f.get("pdf_url"):
            print(f"       PDF: {f['pdf_url'][:80]}")

    # LTZF mapping analysis
    print("\n  --- LTZF Field Coverage ---")
    field_map = {
        "Vorgang.titel": bool(most_stations.get("titel")),
        "Vorgang.typ": bool(most_stations.get("Vorgangstyp")),
        "Vorgang.wahlperiode": True,  # Search parameter
        "Vorgang.verfassungsaendernd": False,  # Not in data
        "Vorgang.initiatoren": bool(most_stations.get("Initiative")),
        "Vorgang.stationen": bool(most_stations.get("fundstellen_parsed")),
        "Vorgang.ids (Vorgangs-ID)": bool(most_stations.get("Vorgangs-ID")),
        "Station.typ": bool(all_station_types),
        "Station.datum": any(f.get("datum") for f in most_stations.get("fundstellen_parsed", [])),
        "Station.gremium (Ausschuss)": bool(all_committees),
        "Station.dokumente (PDF links)": any(
            f.get("pdf_url") for f in most_stations.get("fundstellen_parsed", [])
        ),
        "Dokument.link": True,  # PDF URLs available
        "Dokument.drucksachennr": any(
            f.get("drucksache") for f in most_stations.get("fundstellen_parsed", [])
        ),
        "Dokument.volltext": False,  # Needs PDF download + extraction
    }
    for field, available in field_map.items():
        status = "YES" if available else "NO"
        print(f"    {status:3s}  {field}")

    return results


def test_vorgang_detail_via_search(session: requests.Session, results: list[dict]):
    """Test 2: Try to get detail data via a targeted search for a specific Vorgang."""
    print_separator("TEST 2: Vorgang Detail — Targeted Search")

    # The detail page is SPA-routed, so we can't fetch it directly.
    # Instead, let's try a very specific search to get a single Vorgang with max detail.
    vorgangs_id = None
    for r in results:
        vid = r.get("Vorgangs-ID", "")
        if vid:
            vorgangs_id = vid
            break

    if not vorgangs_id:
        log.error("No Vorgangs-ID found")
        return

    print(f"\n  Attempting to access detail for: {vorgangs_id}")
    print(f"  Detail URL (SPA): https://parlis.landtag-bw.de/parlis/vorgang/{vorgangs_id}")
    print(f"  Note: This is SPA-routed — server returns full page, JS renders detail")

    # Let's check the raw HTML comment data in the search results
    # The HTML contains JSON-like comments with raw field data
    print("\n  --- Raw Data from HTML Comments ---")
    html_content = (OUTPUT_DIR / "gesetzgebung_results.html").read_text(encoding="utf-8")

    # Extract the comment blocks that contain raw data
    comment_pattern = re.compile(r"<!--(\{.*?\})-->", re.DOTALL)
    comments = comment_pattern.findall(html_content)
    print(f"  Found {len(comments)} data comment blocks")

    if comments:
        # Parse the first comment to see what fields are available
        try:
            raw_data = json.loads(comments[0])
            print(f"\n  Raw fields in first record:")
            for key in sorted(raw_data.keys()):
                value = raw_data[key]
                if isinstance(value, list) and value:
                    first = value[0]
                    if isinstance(first, dict):
                        display = str(first.get("main", first))[:80]
                    else:
                        display = str(first)[:80]
                elif isinstance(value, (str, int)):
                    display = str(value)[:80]
                else:
                    display = str(value)[:80]
                print(f"    {key}: {display}")

            # Check specifically for WMV35 which contains the full Fundstellen string
            wmv35 = raw_data.get("WMV35", [{}])
            if wmv35 and isinstance(wmv35, list):
                fundstellen_raw = wmv35[0].get("main", "")
                entries = fundstellen_raw.split(" || ")
                print(f"\n  Fundstellen entries from raw data ({len(entries)}):")
                for entry in entries:
                    # Format: url @@ id @@ mimetype @@ description || id <br>
                    parts = entry.split(" @@ ")
                    if len(parts) >= 4:
                        print(f"    URL: {parts[0].strip()[:80]}")
                        print(f"    ID: {parts[1].strip()}")
                        print(f"    Type: {parts[2].strip()}")
                        print(f"    Desc: {parts[3].strip()[:80]}")
                        print()
        except json.JSONDecodeError as e:
            print(f"  Failed to parse comment JSON: {e}")
            print(f"  First 200 chars: {comments[0][:200]}")


def test_vorgangstyp_discovery(session: requests.Session):
    """Test 3: Discover all available Vorgangstyp values."""
    print_separator("TEST 3: Discover Available Vorgangstypen")

    # All types from the PARLIS dropdown (extracted from vorgang_detail.html)
    known_types = [
        "Aktuelle Debatte",
        "Anmerkung zur Plenarsitzung",
        "Ansprache/Erklärung/Mitteilung",
        "Antrag",
        "Antrag der Landesregierung/eines Ministeriums",
        "Antrag des Rechnungshofs",
        "Bericht des Parlamentarischen Kontrollgremiums",
        "Besetzung externer Gremien",
        "Besetzung interner Gremien",
        "Enquetekommission",
        "EU-Vorlage",
        "Geschäftsordnung",
        "Gesetzgebung",
        "Große Anfrage",
        "Haushaltsgesetzgebung",
        "Immunitätsangelegenheit",
        "Kleine Anfrage",
        "Mitteilung der Landesregierung/eines Ministeriums",
        "Mitteilung des Bürgerbeauftragten",
        "Mitteilung des Landesbeauftragten für den Datenschutz",
        "Mitteilung des Präsidenten",
        "Mitteilung des Rechnungshofs",
        "Mündliche Anfrage",
        "Petitionen",
        "Regierungsbefragung",
        "Regierungserklärung/Regierungsinformation",
        "Schreiben des Bundesverfassungsgerichts",
        "Schreiben des Verfassungsgerichtshofs",
        "Untersuchungsausschuss",
        "Volksantrag",
    ]

    print(f"\n  Testing {len(known_types)} known Vorgangstyp values...\n")
    type_counts = {}  # {type: (count, has_report_id)}

    for vt in known_types:
        time.sleep(REQUEST_DELAY_S)
        report_id, count = search_parlis(session, vorgangstyp=vt)
        if count > 0:
            type_counts[vt] = (count, bool(report_id))
            status = "OK" if report_id else "TOO LARGE (needs date filter)"
            print(f"    {vt:55s} → {count:5d}  [{status}]")
        else:
            print(f"    {vt:55s} → 0")

    print(f"\n  Summary: {len(type_counts)} types with data")
    print(f"\n  Directly fetchable (small result sets):")
    for vt, (count, ok) in sorted(type_counts.items(), key=lambda x: -x[1][0]):
        if ok:
            print(f"    {count:5d}  {vt}")
    print(f"\n  Needs date filtering (large result sets):")
    for vt, (count, ok) in sorted(type_counts.items(), key=lambda x: -x[1][0]):
        if not ok:
            print(f"    {count:5d}  {vt}  (total hits, need date range to paginate)")

    # Test: can we fetch "Kleine Anfrage" with a date filter?
    print("\n  --- Testing date-filtered search for large types ---")
    time.sleep(REQUEST_DELAY_S)
    report_id, count = search_parlis(
        session, vorgangstyp="Kleine Anfrage", start_date="01.01.2026", end_date="15.02.2026"
    )
    if report_id:
        print(f"    Kleine Anfrage (Jan-Feb 2026): {count} results — DATE FILTERING WORKS!")
        time.sleep(REQUEST_DELAY_S)
        html_content = fetch_results(session, report_id, start=0, chunksize=3)
        save_html("kleine_anfrage_sample.html", html_content)
        results = parse_vorgang_results(html_content)
        if results:
            print(f"    Sample fields: {sorted(results[0].keys())}")
            print(f"    Sample title: {results[0].get('titel', '?')[:70]}")
            print(f"    Sample type: {results[0].get('Vorgangstyp', '?')}")
    else:
        print(f"    Kleine Anfrage (Jan-Feb 2026): still too large ({count} hits)")

    return type_counts


def test_ics_calendar(session: requests.Session):
    """Test 4: Analyze ICS calendar data."""
    print_separator("TEST 4: ICS Calendar Analysis")

    ics_url = "https://www.landtag-bw.de/resource/calendar/501552/download/terminkalender.ics"
    try:
        resp = session.get(ics_url, timeout=30)
        resp.raise_for_status()
        ics_content = resp.text
        save_html("terminkalender.ics", ics_content)

        # Parse events
        events = []
        lines = ics_content.split("\n")
        in_event = False
        current_event = {}
        for line in lines:
            line = line.strip()
            if line == "BEGIN:VEVENT":
                in_event = True
                current_event = {}
            elif line == "END:VEVENT":
                in_event = False
                events.append(current_event)
            elif in_event and ":" in line:
                key, _, value = line.partition(":")
                key = key.split(";")[0]
                current_event[key] = value

        print(f"\n  Total events: {len(events)}")

        # Categorize by SUMMARY prefix
        categories = {}
        for e in events:
            summary = e.get("SUMMARY", "")
            cat = summary.split(":")[0] if ":" in summary else summary
            categories.setdefault(cat, []).append(e)

        print(f"\n  Event categories:")
        for cat, cat_events in sorted(categories.items(), key=lambda x: -len(x[1])):
            print(f"    {len(cat_events):3d}  {cat}")

        # Show Plenarsitzung events specifically
        plenar = categories.get("Plenarsitzung", [])
        if plenar:
            print(f"\n  Plenarsitzung events ({len(plenar)}):")
            for e in plenar[:5]:
                start = e.get("DTSTART", "")
                end = e.get("DTEND", "")
                summary = e.get("SUMMARY", "")
                print(f"    {start}–{end}: {summary}")
            if len(plenar) > 5:
                print(f"    ... and {len(plenar) - 5} more")

        # LTZF Sitzung coverage analysis
        print("\n  --- LTZF Sitzung Field Coverage from ICS ---")
        print(f"    {'YES':3s}  Sitzung.termin (DTSTART)")
        print(f"    {'PARTIAL':7s}  Sitzung.gremium (only category, e.g. 'Plenarsitzung')")
        print(f"    {'NO':3s}  Sitzung.nummer")
        print(f"    {'NO':3s}  Sitzung.tops (agenda items)")
        print(f"    {'NO':3s}  Sitzung.public")

    except Exception as e:
        log.error("ICS fetch failed: %s", e)


def print_summary():
    """Print overall findings summary."""
    print_separator("SUMMARY: Data Source Evaluation Results")

    print("""
  ┌─────────────────────────────────────────────────────────────────┐
  │                    PARLIS API FINDINGS                         │
  ├─────────────────────────────────────────────────────────────────┤
  │ Working:                                                       │
  │  • serverrecordname="vorgang" with specific Vorgangstyp filter │
  │  • format="suchergebnis-vorgang-full" (HTML)                   │
  │  • Paginated results via report_id                             │
  │                                                                │
  │ Not Working:                                                   │
  │  • Other serverrecordnames (gesetzentwurf, drucksache, etc.)   │
  │  • Other format values (suchergebnis-vorgang-short, etc.)      │
  │  • Unfiltered search (no Vorgangstyp) stays "running"          │
  │  • Detail pages (SPA-routed, need JS rendering)                │
  │                                                                │
  │ Key Insight:                                                   │
  │  The list view Fundstellen contain rich station data:           │
  │  station type, date, committee, Drucksache number, PDF link    │
  │  → May not need detail pages at all!                           │
  │                                                                │
  │ Additionally, HTML comments contain raw JSON with field codes   │
  │ (EWBV01, WMV30, etc.) that provide additional structured data  │
  ├─────────────────────────────────────────────────────────────────┤
  │                    DATA COVERAGE                               │
  ├─────────────────────────────────────────────────────────────────┤
  │ Vorgang:                                                       │
  │  ✓ titel, typ, wahlperiode, initiatoren, stationen, ids        │
  │  ✗ verfassungsaendernd (must infer from title/content)         │
  │                                                                │
  │ Station:                                                       │
  │  ✓ typ, datum, dokumente (PDF links)                           │
  │  ~ gremium (committee names in Beschlussempfehlung entries)    │
  │                                                                │
  │ Dokument:                                                      │
  │  ✓ link (PDF URLs), drucksachennr                              │
  │  ✗ volltext (needs PDF download + text extraction)             │
  │                                                                │
  │ Sitzung:                                                       │
  │  ~ termin (ICS calendar, dates only)                           │
  │  ✗ nummer, tops, public, gremium details                       │
  ├─────────────────────────────────────────────────────────────────┤
  │                    RECOMMENDED APPROACH                        │
  ├─────────────────────────────────────────────────────────────────┤
  │ 1. Use PARLIS search per Vorgangstyp as primary data source    │
  │ 2. Parse Fundstellen for station progression + documents       │
  │ 3. Parse HTML comments for additional raw field data            │
  │ 4. Download PDFs for Dokument.volltext                          │
  │ 5. Use ICS calendar for basic Sitzung dates                    │
  │ 6. Infer verfassungsaendernd from title keywords               │
  └─────────────────────────────────────────────────────────────────┘
""")


def main():
    print("=" * 70)
    print("  PARLIS API Test Script v2")
    print("  Testing data availability for LTZF BaWue Scraper")
    print("=" * 70)

    ensure_output_dir()

    try:
        session = create_session()
    except Exception as e:
        log.error("Failed to establish session: %s", e)
        sys.exit(1)

    # Test 1: Gesetzgebung search with station analysis
    time.sleep(REQUEST_DELAY_S)
    results = test_gesetzgebung_search(session)

    # Test 2: Detail data from HTML comments
    if results:
        test_vorgang_detail_via_search(session, results)

    # Test 3: Discover all Vorgangstypen
    time.sleep(REQUEST_DELAY_S)
    test_vorgangstyp_discovery(session)

    # Test 4: ICS calendar
    time.sleep(REQUEST_DELAY_S)
    test_ics_calendar(session)

    # Summary
    print_summary()

    print("=" * 70)
    print("  DONE — Check scripts/output/ for saved HTML files")
    print("=" * 70)


if __name__ == "__main__":
    main()
