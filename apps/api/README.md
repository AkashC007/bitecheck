# BiteCheck API

FastAPI backend for BiteCheck.

## Local setup

Run these commands from `apps/api`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install '.[dev]'
```

## Verify

```bash
.venv/bin/ruff check .
.venv/bin/mypy src tests
.venv/bin/pytest
.venv/bin/python -m pip check
```

## Run locally

```bash
.venv/bin/uvicorn --app-dir src bitecheck_api.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Its development health
endpoint is `GET /health`, and interactive documentation is available at
`http://127.0.0.1:8000/docs`.

## Restaurant search

`GET /restaurants/search` reads the validated hybrid JSON dataset. Real
establishment identity and inspection fields come from the City snapshot; all
filters are optional and combine with AND logic:

- `cuisine`: case-insensitive cuisine name
- `maximum_budget`: positive estimated cost per person
- `vegetarian_required`: `true` or `false`; defaults to `false`
- `starting_area`: case-insensitive supported Chicago origin
- `maximum_travel_time`: positive minutes; requires `starting_area`

Example:

```bash
curl 'http://127.0.0.1:8000/restaurants/search?cuisine=Chinese&maximum_budget=25&vegetarian_required=true&starting_area=Illinois%20Tech&maximum_travel_time=30'
```

No matches produce HTTP 200 with an empty `restaurants` list. Invalid filters
produce HTTP 422. Missing or invalid restaurant data produces a safe HTTP 503
without exposing filesystem details.

The optional `RESTAURANT_DATA_PATH` environment variable can point the
repository adapter at another file with the same schema. The committed
synthetic dataset is used by default.

## Natural-language parsing

`POST /restaurants/parse` converts a sentence into the same structured filter
model used by restaurant search:

```bash
curl -X POST 'http://127.0.0.1:8000/restaurants/parse' \
  -H 'Content-Type: application/json' \
  -d '{"text":"Japanese near IIT, veggie, under $25, within 30 minutes"}'
```

The rule-based parser recognizes the ten dataset cuisines, seven starting
areas and documented aliases, dollar budgets, vegetarian wording, and travel
minutes. It normalizes Unicode, case, and whitespace before matching.

The parser deliberately does not interpret subjective words such as `best` or
`authentic`. It does not treat `vegan` as `vegetarian`, because weakening that
requirement could return an unsuitable restaurant. Multiple cuisines, areas,
budgets, or travel limits produce HTTP 422 instead of an arbitrary choice. A
travel limit also requires a recognized starting area.

This implementation follows a parser protocol. A future AI-backed adapter can
replace the rule-based class without changing the endpoint or search-filter
contract. The current parser requires no API key.

## Transportation categories

`GET /restaurants/travel-categories` categorizes all restaurants from one
starting area. `starting_area` is required; all threshold parameters are
optional:

```bash
curl 'http://127.0.0.1:8000/restaurants/travel-categories?starting_area=Illinois%20Tech'
```

Default priority and thresholds are walkable (15 minutes), comfortable walk
(25), easy public transit (30), longer public transit (50), easy drive (20),
then inconvenient. Walking is preferred before transit, and transit before
driving. A category is allowed only when its mode also fits
`maximum_acceptable_minutes`, which defaults to 50.

The response contains the applied thresholds, category counts, all three travel
estimates, the selected category and mode, and a plain-language explanation.
All travel values remain synthetic estimates, not live routing results.

## Explainable ranking

`POST /restaurants/rank` accepts structured filters and optional weights. It
filters first, then returns descending 0–100 scores with every normalized factor,
configured weight, effective weight, contribution, and explanation. Defaults
are versioned in `config/ranking_weights.json`.

Review Confidence is loaded from the validated Milestone 9 analytics artifact
and participates as a 0–100 evidence-reliability factor. Active weights are
renormalized when a factor is not applicable or a restaurant lacks that factor.
Equal totals share a rank and preserve dataset order.

## Review Confidence

`GET /restaurants/review-confidence` returns all 24 restaurant-level confidence
rows. Every row includes seven component scores and contributions, four penalty
rates and deductions, source metrics, the base and final scores, and a clear
statement that this is not a truth score. A missing, malformed, incomplete, or
internally inconsistent artifact returns a safe HTTP 503.

## Recommendation cards

`POST /restaurants/recommendations` accepts the ranking request contract and
returns card-ready results. It joins restaurant details, all ranking factors,
travel decisions, leading positive and negative themes, Review Confidence,
category labels with reasons, and latest synthetic review dates. Missing or
invalid source artifacts fail with safe HTTP 503 responses rather than partial
cards.

## Conversational follow-ups

`POST /restaurants/conversation` accepts a short message and explicit current
state. It recognizes eight documented follow-up intents, updates a copied state,
rebuilds recommendations, and returns the transition explanation with refreshed
cards. Unsupported language and missing travel context return HTTP 422 instead
of a guessed interpretation. No API key, model, cookie, or server-side user
session is involved.
