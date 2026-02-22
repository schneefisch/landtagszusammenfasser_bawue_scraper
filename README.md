# BaWue Scraper

[![CI](https://github.com/schneefisch/landtagszusammenfasser_bawue_scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/schneefisch/landtagszusammenfasser_bawue_scraper/actions/workflows/ci.yml)
![Coverage](https://raw.githubusercontent.com/schneefisch/landtagszusammenfasser_bawue_scraper/badges/badge-coverage.svg)

Collector for the Baden-Württemberg state parliament ([Landtag BW](https://www.landtag-bw.de/)) as part of
the [Parlamentszusammenfasser](https://codeberg.org/PaZuFa/parlamentszusammenfasser) (PaZuFa/LTZF) platform. Scrapes
legislative proceedings (Vorgänge), documents, and session calendars from the PARLIS system and delivers them to the
LTZF backend via its REST API.

## Prerequisites

- Python 3.13+
- Tesseract OCR with German language pack (for PDF fallback extraction)
- A running LTZF backend instance (for integration tests and production use)

## Setup

```bash
# Clone and enter the project
git clone <repo-url>
cd landtagszusammenfasser_bawue_scraper

# Create virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Install pip-tools for managing lock files (not included in dev extras)
pip install pip-tools

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your LTZF API credentials
```

## Usage

```bash
# Show available options
python -m bawue_scraper --help

# Run full scraping cycle
python -m bawue_scraper

# Scrape only a specific Vorgangstyp
python -m bawue_scraper --type "Gesetzgebung"

# Scrape a specific date range
python -m bawue_scraper --date-from 01.01.2026 --date-to 31.01.2026

# Scrape only Vorgänge (skip calendar)
python -m bawue_scraper --vorgaenge-only

# Scrape only calendar/session data
python -m bawue_scraper --kalender-only
```

## Configuration

All configuration is via environment variables (or a `.env` file). See [.env.example](.env.example) for all options.

| Variable                 | Required | Description                                             |
|--------------------------|----------|---------------------------------------------------------|
| `LTZF_API_URL`           | Yes      | LTZF backend base URL                                   |
| `LTZF_API_KEY`           | Yes      | API key with `collector` scope                          |
| `COLLECTOR_ID`           | Yes      | Unique identifier for this collector instance           |
| `SCRAPE_INTERVAL_HOURS`  | No       | Interval between scraping cycles (default: 24)          |
| `PARLIS_REQUEST_DELAY_S` | No       | Delay between PARLIS requests in seconds (default: 1.0) |
| `LOG_LEVEL`              | No       | Logging level (default: INFO)                           |
| `CACHE_DIR`              | No       | Directory for persistent cache (default: `./cache`)     |

## Development

### Running tests

```bash
# Unit tests only (default, fast)
pytest

# With coverage
pytest --cov=bawue_scraper

# Include integration tests (requires running LTZF backend via scripts/start.sh)
pytest -m integration

# Include slow tests (requires internet, hits live PARLIS)
pytest -m slow

# All tests
pytest -m ""
```

### Linting and formatting

```bash
ruff check src/ tests/        # lint
ruff check --fix src/ tests/  # lint with auto-fix
ruff format src/ tests/       # format
```

### Docker

```bash
docker build -t bawue-scraper .
docker run --env-file .env bawue-scraper
```

### Local LTZF backend

```bash
scripts/start.sh   # start local LTZF backend (Docker)
scripts/stop.sh    # stop it
```

## Project Structure

```
src/bawue_scraper/
├── __main__.py          # CLI entrypoint (argparse)
├── config.py            # pydantic-settings configuration
├── orchestrator.py      # Pipeline coordinator
├── domain/
│   ├── enums.py         # Stationstyp, Vorgangstyp, Dokumententyp
│   └── models.py        # Vorgang, Station, Dokument, Sitzung, Gremium, Autor, Top
├── ports/               # Abstract interfaces (hexagonal architecture)
│   ├── vorgang_source.py
│   ├── document_extractor.py
│   ├── calendar_source.py
│   ├── ltzf_api.py
│   └── cache.py
├── adapters/            # Concrete implementations
│   ├── parlis_adapter.py
│   ├── pdf_extractor.py
│   ├── ics_adapter.py
│   ├── ltzf_client.py
│   └── cache_manager.py
└── mapping/
    └── enum_mapper.py   # PARLIS → LTZF enum mapping
```

## Architecture

The scraper follows a **hexagonal (ports & adapters)** architecture. The domain core defines interfaces (ports) that are
implemented by adapters for external systems. See [docs/architecture.md](docs/architecture.md) for the full architecture
documentation.

**Data sources:**

- **PARLIS** — undocumented JSON/HTML API at `parlis.landtag-bw.de` (primary source for Vorgänge)
- **PDFs** — Drucksachen from `landtag-bw.de` (fulltext extraction via pdfplumber/OCR/LLM)
- **ICS Calendar** — parliamentary session dates

**Data delivery:**

- `PUT /api/v2/vorgang` — submit legislative proceedings
- `PUT /api/v2/kalender/{parlament}/{datum}` — submit session data

## Links

### PaZuFa / Parlamentszusammenfasser (Codeberg)

> **Note:** The project has migrated from GitHub to [Codeberg](https://codeberg.org/PaZuFa). The old GitHub repositories
> are archived.

* [PaZuFa Organization](https://codeberg.org/PaZuFa)
* [parlamentszusammenfasser](https://codeberg.org/PaZuFa/parlamentszusammenfasser) — Main project (formerly
  `landtagszusammenfasser`)
* [pazufa-collector](https://codeberg.org/PaZuFa/pazufa-collector) — Reference collector (formerly `ltzf-collector`)
* [pazufa-backend](https://codeberg.org/PaZuFa/pazufa-backend) — Backend service (formerly `ltzf-backend`)

### General

* [Bundestagszusammenfasser](https://bundestagszusammenfasser.de/)
* [Landtag BaWue](https://www.landtag-bw.de/)

### PaZuFa Documentation

* [Parlamentszusammenfasser docs](https://codeberg.org/PaZuFa/parlamentszusammenfasser/src/branch/main/docs/README.md)
* [OpenAPI-Spezifikation](https://codeberg.org/PaZuFa/parlamentszusammenfasser/src/branch/main/docs/specs/openapi.yml)
* [Authentication](https://codeberg.org/PaZuFa/parlamentszusammenfasser/src/branch/main/docs/authentication.md)
* [CONTRIBUTING](https://codeberg.org/PaZuFa/parlamentszusammenfasser/src/branch/main/CONTRIBUTING.md)
* [SETUP](https://codeberg.org/PaZuFa/parlamentszusammenfasser/src/branch/main/SETUP.md)

### Project Documentation

* [Anforderungen](docs/anforderungen.md) — Datenmodelle, API-Endpunkte, Enumerationen, Datenquellen
* [Architecture](docs/architecture.md) — System overview, hexagonal architecture, data flow, enum mapping

