# system-dashboard

Live system health dashboard for the eight-organ organvm system.

## Overview

A FastAPI web application that reads data from the organvm-corpvs-testamentvm corpus and presents live system health, registry browsing, dependency graphs, soak test trends, essay feeds, and an omega scorecard — all in a brutalist CMYK aesthetic.

## Pages

| Route | Description |
|-------|-------------|
| `/health/` | System health overview with organ breakdown |
| `/registry/` | Registry browser with organ/status/tier filters |
| `/graph/` | Dependency graph with cross-organ analysis |
| `/soak/` | Soak test (VIGILIA) monitoring with CI trends |
| `/essays/` | Essay feed from public-process |
| `/omega/` | Omega scorecard — 8 system completion criteria |

## Quick Start

```bash
pip install -e ".[dev]"
uvicorn dashboard.app:app --reload
```

Open http://localhost:8000

## API Endpoints

- `GET /health/api` — JSON system health data
- `GET /graph/api` — JSON dependency graph
- `GET /registry/api/{repo_name}` — JSON single repo details

## Tech Stack

- **FastAPI** + **Jinja2** + **HTMX** — server-rendered, no JS framework
- Reads JSON/YAML from organvm-corpvs-testamentvm
- Brutalist CMYK design (cyan/magenta/yellow on black)

## Development

```bash
pytest tests/ -v
```
