# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

See [root CLAUDE.md](../../CLAUDE.md) for base instructions!

## Project Overview

BaWue Scraper is a Python collector for the Parlamentszusammenfasser (PaZuFa, formerly LTZF) platform. It scrapes
legislative data (Vorgänge, Drucksachen, sessions) from the Baden-Württemberg PARLIS system and delivers it to the
PaZuFa backend via REST API. The project has migrated from GitHub to [Codeberg](https://codeberg.org/PaZuFa).

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run
python -m bawue_scraper --help
python -m bawue_scraper                          # full scraping cycle
python -m bawue_scraper --type "Gesetzgebung"     # specific Vorgangstyp
python -m bawue_scraper --vorgaenge-only          # skip calendar
python -m bawue_scraper --kalender-only           # skip Vorgänge

# Tests (unit tests run by default; integration/slow excluded)
pytest                                            # unit tests only
pytest tests/unit/test_orchestrator.py             # single file
pytest tests/unit/test_orchestrator.py::TestClass::test_name  # single test
pytest -m integration                             # requires local PaZuFa backend
pytest -m slow                                    # requires internet (live PARLIS)
pytest -m ""                                      # all tests
pytest --cov=bawue_scraper                        # with coverage

# Lint & Format
ruff check src/ tests/                            # lint
ruff check --fix src/ tests/                      # lint with auto-fix
ruff format src/ tests/                           # format

# Docker
docker build -t bawue-scraper .
docker run --env-file .env bawue-scraper

# Local PaZuFa backend for integration tests
./scripts/setup.sh    # one-time: clone PaZuFa repo
./scripts/start.sh    # start backend (Docker)
./scripts/stop.sh     # stop backend
```

## Architecture

**Hexagonal (Ports & Adapters)** — domain core is isolated from external systems.

```
Orchestrator (pipeline coordinator)
  ├── VorgangSource port  ←  ParlisAdapter   (PARLIS JSON API + HTML scraping)
  ├── DocumentExtractor   ←  PdfExtractor    (3-stage: pdfplumber → OCR → LLM)
  ├── CalendarSource      ←  IcsAdapter      (ICS calendar parsing)
  ├── LtzfApi port        ←  LtzfClient      (HTTP client to PaZuFa backend)
  └── Cache port          ←  CacheManager    (file-based or in-memory)
```

**Key layout:**

- `src/bawue_scraper/ports/` — abstract interfaces (ABCs)
- `src/bawue_scraper/adapters/` — concrete implementations
- `src/bawue_scraper/domain/` — Pydantic models (`Vorgang`, `Station`, `Dokument`, `Sitzung`, etc.) and enums
- `src/bawue_scraper/mapping/enum_mapper.py` — PARLIS → PaZuFa enum conversions
- `src/bawue_scraper/orchestrator.py` — coordinates the full scraping pipeline
- `src/bawue_scraper/config.py` — pydantic-settings config from env vars / `.env`

## Configuration

Environment variables (see `.env.example`). Key required vars: `LTZF_API_URL`, `LTZF_API_KEY`, `COLLECTOR_ID`. Optional:
`PARLIS_REQUEST_DELAY_S`, `CACHE_DIR`, `WAHLPERIODE`.

## Testing Conventions

- Tests use `responses` library for HTTP mocking and `pytest-mock` for dependency injection
- `tests/conftest.py` provides shared fixtures (config, sample domain models, adapter mocks)
- Markers: `@pytest.mark.integration` (needs PaZuFa backend), `@pytest.mark.slow` (needs internet)
- New adapters: mock the port interface, test independently

## Tech Stack

Python 3.13+ · Pydantic · requests · lxml · pdfplumber · pytesseract · icalendar · Ruff (lint+format) · pytest · Docker
with Tesseract OCR

## Coding Practices

- **TDD**: Write tests first, then implement
- **Format before commit**: `ruff format src/ tests/` and `ruff check src/ tests/`
- Follow hexagonal architecture: new external integrations get a port interface + adapter implementation
- All domain data uses Pydantic models with validation
- Single Vorgang failures must not stop the pipeline (error tolerance pattern)
