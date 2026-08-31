# Data pipeline

## Hybrid identity and enrichment flow

```text
City of Chicago Food Inspections API (4ijn-s7e5)
                  │ bounded date/location query
                  ▼
scripts/ingest_chicago_food_inspections.py
                  │ clean + license dedupe + newest-result check
                  ▼
data/raw/chicago_food_inspections.json
                  │
                  ▼
scripts/generate_demo_data.py + fixed seed
                  │ synthetic recommendation enrichment
                  ▼
data/synthetic/restaurants.json -> analytics transformations
```

## Run

From the BiteCheck root:

```bash
apps/api/.venv/bin/python scripts/generate_demo_data.py
apps/api/.venv/bin/pytest tests/test_chicago_food_inspections.py tests/test_demo_data.py
```

To refresh the committed source snapshot, run
`scripts/ingest_chicago_food_inspections.py` first. The Socrata endpoint works
without a token; `CHICAGO_DATA_APP_TOKEN` is an optional backend-only rate-limit
token.

## Inputs

- Official dataset: City of Chicago Food Inspections (`4ijn-s7e5`)
- Fixed source window: 2024-01-01 through 2026-08-30
- Seven configured Chicago demo-area centers and 3 km maximum distance
- Seed: 42 and restaurant count: 24 by default

## Transformations

1. Validate and normalize public inspection rows.
2. Group rows by City license and identify the newest inspection in the window.
3. Retain nearby restaurant facilities whose newest result is `Pass` or
   `Pass w/ Conditions`, then select a balanced 24-record snapshot.
4. Preserve real name, address, coordinates, license, and inspection history.
5. Add deterministic synthetic cuisine, price, dietary, rating, review-count,
   opening-hour, and travel fields.
6. Serialize lineage metadata and records with stable ordering.

## Output and lineage

The raw snapshot records source URL, attribution, retrieval date, filters,
modifications, and disclaimers. The enriched file records the source snapshot
date alongside its seed, versions, and exact list of synthetic fields.

For seed 42 and 24 records, repeated runs produced the same SHA-256 hash:

```text
af1e2ff1b3aaa817f851a8ce4cd39c771055bedc72f308d39a291c929f4cc6b3
```

## Current limitations

- This is a fixed batch snapshot, not live business-status data.
- Travel values are estimates for testing, not routing-provider results.
- The source may contain duplicates or corrections, and inspection results only
  describe conditions observed at inspection time.
- Cuisine and all recommendation/profile signals remain synthetic; they must
  not be interpreted as claims about a real establishment.
- No incremental processing, quarantine table, or database exists yet.

## Milestone 2 serving flow

The API reads the committed JSON through a repository adapter, validates the
full document with Pydantic, and checks the metadata record count before every
search. The search service then applies optional filters in dataset order and
returns only typed response fields. This is a small serving layer over the
Milestone 1 artifact; it is not yet an ingestion or database pipeline.

## Milestone 7 review generation

`scripts/generate_review_data.py` reads restaurant branches, then combines a
local random generator seeded with 84, a fixed reference date, cuisine-specific
dishes, and sentiment/aspect blueprints. It writes sorted, indented JSON with no
generation timestamp. Exact and near-duplicate parent IDs, old-review rules, and
burst-group membership preserve row-level lineage for later ETL evaluation.

## Milestone 8 analytics transformation

`scripts/analyze_review_themes.py` reads raw synthetic review text and writes
`data/analytics/review_themes.json`. Review-level rows retain normalized text,
evidence clauses, themes, and sentiment. The aggregate layer contains mention
and sentiment counts. An evaluation layer compares predictions with separate
synthetic labels and records precision, recall, and F1.

## Milestone 9 confidence transformation

`scripts/calculate_review_confidence.py` joins reviews to restaurant branches
and theme counts, computes seven normalized supporting components, applies four
capped penalty rates, and writes a deterministic restaurant-level analytics
artifact. The fixed reference date prevents recency from drifting between runs.

The serving repository validates the entire artifact before the API exposes it.
The committed output contains 24 unique restaurant rows and 288 contributing
reviews. Repeated generation produced SHA-256:

```text
3abf20581ec192fa6f5b4b6a3ce7c3b3b584dc4b6a4ca99fd57ff4aa404c5e37
```

## Milestone 10 presentation insight build

`scripts/build_recommendation_insights.py` joins theme predictions to review
lineage, excludes exact duplicates from display-theme frequencies, selects the
three leading positive and negative themes per restaurant, and records each
restaurant's latest review date. The deterministic artifact is stored at
`data/analytics/recommendation_insights.json` and validates before serving.

Its current SHA-256 is:

```text
3037c2f6067dbdfafa155e4ce8b85a8cdd9363480d7dc20f8df0cbb02bc98e20
```
