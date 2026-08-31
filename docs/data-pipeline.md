# Data pipeline

## Milestone 1 generation flow

```text
Versioned constants + seed + record count
                  │
                  ▼
scripts/generate_demo_data.py
                  │
     balanced category assignments
     bounded coordinate variation
     synthetic cost and dietary rules
     Haversine distance calculation
     synthetic travel-time calculation
                  │
                  ▼
data/synthetic/restaurants.json
                  │
                  ▼
tests/test_demo_data.py
```

## Run

From the BiteCheck root:

```bash
apps/api/.venv/bin/python scripts/generate_demo_data.py
apps/api/.venv/bin/pytest
```

## Inputs

- Seed: 42 by default
- Restaurant count: 24 by default
- Versioned neighborhood centers, cuisine values, price ranges, name fragments,
  and fictional street names stored in the generator

## Transformations

1. Balance neighborhoods, cuisines, and price categories before shuffling.
2. Add bounded coordinate offsets around configured Chicago-area centers.
3. Apply price, dietary, rating, review-count, and opening-hour rules.
4. Calculate straight-line Haversine distance from each supported origin.
5. Convert distance into clearly synthetic walk, transit, and drive estimates.
6. Serialize JSON with sorted keys and stable indentation.

## Output and lineage

The committed JSON records its seed, schema version, generator version, record
count, city, and synthetic status. It intentionally omits a generation timestamp
because timestamps would make identical runs produce different bytes.

For seed 42 and 24 records, repeated runs produced the same SHA-256 hash:

```text
e9f17701e6bd3e1d42a9d9a6885a164d317cd5c546c328ac852be6419afa4b8f
```

## Current limitations

- This is batch generation, not external API ingestion.
- Travel values are estimates for testing, not routing-provider results.
- Coordinates and addresses are fictional.
- No incremental processing, raw/clean/analytics layers, quarantine, or database
  exists yet.

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
577444691784b4a4eac70151145a067da424efa28dd922b8f10c09bfd1035993
```

## Milestone 10 presentation insight build

`scripts/build_recommendation_insights.py` joins theme predictions to review
lineage, excludes exact duplicates from display-theme frequencies, selects the
three leading positive and negative themes per restaurant, and records each
restaurant's latest review date. The deterministic artifact is stored at
`data/analytics/recommendation_insights.json` and validates before serving.

Its current SHA-256 is:

```text
e5b2b4334f35db4cc14be117eb4493c89c4782cb85762da7743dfbee639c353d
```
