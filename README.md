# BiteCheck

BiteCheck is an explainable restaurant recommendation app built with a typed
FastAPI backend, a Next.js interface, and a reproducible hybrid-data pipeline
layered on an official City of Chicago data snapshot. It ranks real
Chicago establishments using clearly labeled demo recommendation signals—then
shows why each result ranked where it did.

![BiteCheck real-data recommendation results](docs/assets/bitecheck-showcase-real-data.jpg)

> Names, addresses, coordinates, and inspection records come from the City of
> [Chicago Food Inspections dataset](https://data.cityofchicago.org/Health-Human-Services/Food-Inspections/4ijn-s7e5)
> (snapshot: 2026-08-30). Cuisines, prices,
> dietary flags, ratings, reviews, hours, travel times, themes, confidence, and
> ranking labels are synthetic. Inspection records are point-in-time findings,
> not a guarantee of current operation or safety.

## What it demonstrates

- Reproducible Python ingestion, cleaning, deduplication, enrichment, and
  analytics pipelines over 22,003 public inspection rows
- Explainable ranking with configurable weights and per-factor score
  contributions
- Review-theme extraction with a measured synthetic baseline of 0.9825 F1
- A transparent Review Confidence model with seven supporting components and
  four penalties
- Typed FastAPI endpoints, Pydantic validation, repository/service separation,
  and safe failure states
- A responsive Next.js and TypeScript interface with browser-only location
  distance, stackable deterministic follow-ups, and optional voice controls
- Automated CI for linting, strict type checks, tests, production builds, and
  dependency auditing

## Project snapshot

| Area | Result |
| --- | --- |
| Hybrid data | 24 real establishments, 288 synthetic reviews, 15 themes |
| Automated tests | 169 total: 146 Python and 23 TypeScript |
| Quality gates | Ruff, strict mypy, ESLint, production build, npm audit |
| External services | None required; no API keys or paid providers |
| Current state | Showcase-ready MVP with local and container run paths |

Detailed measurements and their limitations are recorded in
[docs/resume-metrics.md](docs/resume-metrics.md).

## Architecture

```text
City open data -> cleaned snapshot -> synthetic enrichment -> analytics
                                                        |
Browser -> Next.js server routes -> FastAPI services -> ranked explanations
```

The browser talks only to same-origin Next.js routes. Next.js reads the
server-only `API_BASE_URL` and forwards requests to FastAPI, so backend
configuration is never shipped to the browser.

The optional “Use my location” control keeps coordinates in browser memory. It
uses them only to show straight-line distance to the 24 records and to reorder
the current matches; coordinates are never sent to FastAPI or stored.

## Run locally

Requirements: Python 3.11+ and the Node version listed in `.node-version`.

```bash
# Terminal 1 — backend
cd apps/api
python3 -m venv .venv
.venv/bin/python -m pip install '.[dev]'
.venv/bin/uvicorn --app-dir src bitecheck_api.main:app --reload

# Terminal 2 — frontend
cd apps/web
npm ci
npm run dev
```

Open `http://localhost:3000`. Interactive API documentation is available at
`http://localhost:8000/docs`. The committed demo data is ready to use; no API
key or `.env` file is needed for the default local setup.

## Verify

```bash
# From the project root
apps/api/.venv/bin/ruff check .
apps/api/.venv/bin/mypy scripts apps/api/src apps/api/tests tests
apps/api/.venv/bin/pytest

cd apps/web
npm test
npm run lint
npm run build
npm audit --omit=dev --audit-level=high
```

GitHub Actions runs the same checks on every push and pull request.

## Regenerate the analytics data

Run from the project root:

```bash
apps/api/.venv/bin/python scripts/generate_demo_data.py
apps/api/.venv/bin/python scripts/generate_review_data.py
apps/api/.venv/bin/python scripts/analyze_review_themes.py
apps/api/.venv/bin/python scripts/calculate_review_confidence.py
apps/api/.venv/bin/python scripts/build_recommendation_insights.py
```

The real-source snapshot is committed for reproducible builds. To refresh it
from the public City API first, run
`scripts/ingest_chicago_food_inspections.py`; no API token is required.

Fixed seeds and reference dates make the artifacts reproducible. The pipeline,
schemas, assumptions, and limitations are documented in
[docs/data-pipeline.md](docs/data-pipeline.md),
[docs/data-dictionary.md](docs/data-dictionary.md), and
[docs/privacy-and-ethics.md](docs/privacy-and-ethics.md).

## Deployment

The repository includes a two-service Render Blueprint, a production backend
`Dockerfile`, and standard Next.js production commands. Both services can be
created together on Render's free plan:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2FAkashC007%2Fbitecheck)

See [docs/deployment.md](docs/deployment.md) for the service connection,
environment variables, free-tier behavior, and public smoke checks.

## More documentation

- [Architecture](docs/architecture.md)
- [Ranking methodology](docs/ranking-methodology.md)
- [Review Confidence methodology](docs/review-confidence-methodology.md)
- [Conversation methodology](docs/conversation-methodology.md)
- [Project decisions](docs/project-decisions.md)
