# BiteCheck

BiteCheck is a live Chicago restaurant-inspection explorer and an explainable
analytics portfolio built with FastAPI, Next.js, TypeScript, and Python. Its
primary experience queries official City records for real nearby establishments.
A separate Analytics Lab preserves the reproducible synthetic review, ranking,
and recommendation work without presenting it as public fact.

![BiteCheck synthetic Analytics Lab results](docs/assets/bitecheck-showcase-real-data.jpg)

> The public explorer queries the City of
> [Chicago Food Inspections dataset](https://data.cityofchicago.org/Health-Human-Services/Food-Inspections/4ijn-s7e5)
> live. The Analytics Lab uses a reproducible 2026-08-30 identity snapshot;
> its cuisines, prices, dietary flags, ratings, reviews, hours, travel times,
> themes, confidence, and ranking labels are synthetic. Inspection records are
> point-in-time findings, not guarantees of current operation or safety.

## What it demonstrates

- Reproducible Python ingestion, cleaning, deduplication, enrichment, and
  analytics pipelines over 22,003 public inspection rows
- A replaceable live SODA provider with external-row validation, license-level
  entity resolution, geographic search, distance ordering, and safe failures
- Explainable ranking with configurable weights and per-factor score
  contributions
- Review-theme extraction with a measured synthetic baseline of 0.9825 F1
- A transparent Review Confidence model with seven supporting components and
  four penalties
- Typed FastAPI endpoints, Pydantic validation, repository/service separation,
  and safe failure states
- A responsive public inspection explorer plus a visibly separate synthetic
  Analytics Lab with stackable follow-ups and optional voice controls
- Automated CI for linting, strict type checks, tests, production builds, and
  dependency auditing

## Project snapshot

| Area | Result |
| --- | --- |
| Live public data | City inspection queries with up to 50 deduplicated establishments |
| Analytics Lab | 24 real identities, 288 synthetic reviews, 15 themes |
| Automated tests | 181 total: 152 Python and 29 TypeScript |
| Quality gates | Ruff, strict mypy, ESLint, production build, npm audit |
| External services | City of Chicago public API; no key or paid provider |
| Current state | Public-use-ready Chicago explorer; hosting account still required |

Detailed measurements and their limitations are recorded in
[docs/resume-metrics.md](docs/resume-metrics.md).

## Architecture

```text
Public explorer: Browser -> Next.js -> FastAPI -> live City API
                                              -> validate -> dedupe -> factual cards

Analytics Lab:  City snapshot -> synthetic enrichment -> analytics
                                                        -> explainable demo cards
```

The browser talks only to same-origin Next.js routes. Next.js reads the
server-only `API_BASE_URL` and forwards requests to FastAPI, so backend
configuration is never shipped to the browser.

In the public explorer, “Use my current location” sends coordinates through the
same-origin Next.js route and FastAPI to perform the live geographic City query;
BiteCheck does not persist them. Preset Chicago areas share no personal
location. The separate Analytics Lab still calculates its fixed-snapshot
distance entirely in the browser.

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
`http://localhost:8000/docs`. The public explorer needs internet access to the
City service. No API key or `.env` file is needed for the default local setup;
the committed Analytics Lab data also works reproducibly.

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
- [Public inspection explorer](docs/public-inspection-explorer.md)
- [Ranking methodology](docs/ranking-methodology.md)
- [Review Confidence methodology](docs/review-confidence-methodology.md)
- [Conversation methodology](docs/conversation-methodology.md)
- [Project decisions](docs/project-decisions.md)
