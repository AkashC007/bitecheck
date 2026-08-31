# Resume metrics

Only measured results belong in this file.

## Milestone 0 measurements

- Backend endpoint tests: 1 passed
- Local health endpoint HTTP status: 200
- Frontend-to-backend states verified: 2 (connected and unavailable)

At Milestone 0 completion, no restaurant, review, pipeline, recommendation, or
user-behavior metrics existed.

## Milestone 1 measurements

- Synthetic restaurant records generated: 24
- Cuisine categories represented: 10
- Chicago starting areas represented: 7
- Origin-to-restaurant travel estimates generated: 168
- Vegetarian-available records: 20
- Vegan-available records: 7
- Price distribution: 8 `$`, 8 `$$`, and 8 `$$$`
- Records passing current validation rules: 24/24 (100%)
- Project tests passing after Milestone 1: 7
- Repeated same-seed file hashes matched: yes
- Observed local generator runtime: 0.15 seconds for 24 records

The runtime is one local measurement on the development machine, not a
production performance guarantee. No review, recommendation, pipeline-success,
or user-behavior metrics exist yet.

## Milestone 2 measurements

- Structured search filters implemented: 5
- Synthetic restaurant records searchable: 24
- Focused restaurant-search tests passing: 12
- Total project tests passing after Milestone 2: 19
- Live OpenAPI path check: 2 paths (`/health`, `/restaurants/search`)
- Observed local multi-filter response time: 0.015 seconds

The response time is one local measurement on the development machine, not a
benchmark or production performance guarantee. No ranking, review, database,
or user-behavior metrics exist yet.

## Milestone 3 measurements

- Structured frontend controls implemented: 5
- Frontend contract tests passing: 5
- Total automated project tests passing: 24 (19 Python, 5 TypeScript)
- Suggested-preference matches rendered end to end: 8
- Browser outcome states verified: 3 (results, no matches, service unavailable)
- Responsive viewport checked: 390 pixels wide
- Horizontal overflow at 390 pixels: none
- Browser console errors and warnings during final verification: 0

These are implementation and local verification measurements, not production
traffic or user-engagement metrics. Ranking, review, database, and user-behavior
metrics still do not exist.

## Milestone 4 measurements

- Natural-language filter types supported: 5
- Canonical cuisines recognized: 10
- Canonical Chicago starting areas recognized: 7
- Focused parser and endpoint tests passing: 38
- Total automated project tests passing after Milestone 4: 62
- Full product example filters extracted correctly: 5/5
- Observed local parse endpoint response time: 0.005 seconds
- Parsed Japanese example search matches: 2

The parser time is one local observation, not a production benchmark. No AI
model, paid API, production-language corpus, ranking, review, or user-behavior
metric exists yet.

## Milestone 5 measurements

- Transportation categories implemented: 6
- Configurable threshold values: 6
- Focused transportation tests passing: 19
- Total automated project tests passing after Milestone 5: 81
- Restaurants categorized for Illinois Tech: 24/24 (100%)
- Default Illinois Tech distribution: 4 walkable, 5 comfortable walk, 12 easy
  public transit, 3 longer public transit, 0 easy drive, 0 inconvenient
- Category-count reconciliation: 24/24 records
- Observed local categorization response time: 0.006 seconds

Travel values remain synthetic and the response time is one local observation,
not a routing-accuracy claim or production benchmark.

## Milestone 6 measurements

- Ranking factors modelled: 6
- Focused ranking tests passing: 12
- Suggested-preference matches ranked: 8
- Top result: Little Sakura Kitchen, 82.0/100
- Observed local ranking response time: 0.005 seconds
- Total automated tests after Milestone 6: 93

## Milestone 7 measurements

- Synthetic review records: 288 across 24 branches and 3 sources
- Source distribution: 96 reviews per source
- Sentiment distribution: 147 positive, 69 negative, 72 mixed
- Controlled exact duplicates: 24; near-duplicates: 24; old reviews: 24
- Suspicious burst records: 24 across 6 groups
- Planned aspect themes represented: 15/15
- Focused review-data tests passing: 9
- Total automated project tests after Milestone 7: 102
- Repeated seed-84 review file hashes matched: yes

These counts describe controlled synthetic data, not real customer behavior or
production fraud prevalence.

## Milestone 8 measurements

- Reviews analyzed: 288/288 (100%)
- Themes covered: 15/15
- Expected aspect-sentiment pairs: 672
- Predicted pairs: 696; exact true-positive pairs: 672
- Synthetic baseline precision: 0.9655
- Synthetic baseline recall: 1.0000
- Synthetic baseline F1: 0.9825
- Focused review-theme tests passing: 9

These metrics use controlled template text and must not be presented as
real-world NLP performance.

## Milestone 9 measurements

- Restaurant confidence rows calculated: 24/24 (100%)
- Contributing synthetic reviews: 288
- Supporting components exposed per restaurant: 7
- Penalty components exposed per restaurant: 4
- Score range: 69.22–75.76; mean: 71.93
- Confidence bands: 1 high, 23 medium, 0 low
- Restaurants receiving controlled burst penalties: 6
- Confidence output SHA-256 reproducible: yes
- Focused confidence calculation and API tests: 11
- Total automated tests after Milestone 9: 122 (117 Python, 5 TypeScript)

These values measure a controlled synthetic evidence model. They do not measure
review truthfulness, fraud-detection accuracy, or real customer reliability.

## Milestone 10 measurements

- Card-ready restaurant insight rows: 24/24
- Exact duplicate reviews excluded from display-theme counts: 24
- Positive themes displayed per card: up to 3
- Negative themes displayed per card: up to 3
- Recommendation categories implemented and assigned in suggested search: 8/8
- Suggested-preference recommendation cards: 8
- Focused new Milestone 10 tests: 16 (11 Python, 5 TypeScript)
- Total automated project tests: 138 (128 Python, 10 TypeScript)
- Browser outcome states verified: ranked results and empty results
- Responsive layouts verified: narrow single column and 1440-pixel three column
- Horizontal overflow in narrow check: none
- Browser console errors and warnings: 0

These are local implementation and synthetic-data measurements, not production
engagement, conversion, or recommendation-quality results.

## Milestone 11 measurements

- Deterministic follow-up intents implemented: 8
- Explicit conversation-state dimensions: filters, sort, travel, theme, limit
- Suggested-search walkable candidates: 4 of 8
- Verified chained transitions: walkable then cheapest
- Focused conversation tests: 14
- Total automated project tests: 152 (142 Python, 10 TypeScript)
- Paid model or API calls required: 0

These measurements verify deterministic behavior on synthetic data. They do not
measure natural-language coverage, production conversation quality, or user
satisfaction.

## Milestone 12 implementation measurements (live microphone check pending)

- Voice-adapter tests passing: 4
- Total automated project tests: 156 (142 Python, 14 TypeScript)
- Live non-microphone states verified: editable transcript, text submission,
  spoken-reply toggle, stop control, and supported-browser control visibility
- Horizontal overflow in narrow voice-control layout: none
- Browser console errors and warnings: 0
- Paid voice API keys required: 0

No microphone recording, recognition accuracy, or permission outcome is claimed
until the user-authorized live check is completed.

## Public deployment hardening

- Server-only hosting configuration tests: 3
- Total automated project tests: 159 (142 Python, 17 TypeScript)
- Render services defined: 2 (FastAPI and Next.js)
- Production npm audit vulnerabilities: 0

These are repository and local verification measurements. Public uptime and
traffic are not claimed until the deployment is live and observed.
