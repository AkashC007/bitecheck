# Learning journal

## Milestone 0 — Development environment and architecture

### Concepts learned

- The frontend renders browser UI; the backend owns validation, business logic,
  future data access, and secrets.
- An HTTP endpoint is a contract made from a method, path, status, content type,
  and response body.
- Environment variables without `NEXT_PUBLIC_` remain on the Next.js server.
- TypeScript, Pydantic, linting, type checking, and tests catch different kinds
  of defects.
- A health check verifies service availability, not restaurant functionality.

### Features completed

- Next.js 16 frontend with a responsive BiteCheck health page.
- FastAPI backend with typed `GET /health` output.
- Server-side Next.js-to-FastAPI health integration.
- Safe backend unavailable state with a two-second timeout.
- Frontend build/lint checks and backend lint/type/test/dependency checks.

### Commands used

- `npm run dev`, `npm run lint`, and `npm run build`
- `.venv/bin/uvicorn --app-dir src bitecheck_api.main:app --reload`
- `.venv/bin/pytest`, `.venv/bin/ruff check .`, and
  `.venv/bin/mypy src tests`
- `curl` for local HTTP smoke tests
- `git status` and `git check-ignore` for repository safety checks

### Errors encountered and solved

- Node.js was missing, so Node.js 24 LTS was installed and pinned.
- The first Next.js scaffold attempt failed because `apps/` did not exist; the
  directory was created before retrying.
- Initial npm downloads were slow but continued returning successful registry
  responses, so the same installation was allowed to finish.
- Starlette deprecated the old `httpx` test fallback; the development
  dependency was changed to `httpx2`.
- Python 3.14 skipped a macOS-hidden editable `.pth` file. pytest and Uvicorn now
  use an explicit `src` path, and the package uses a normal local install.

### Questions I should now be able to answer

- What responsibilities belong to the frontend and backend?
- What does `GET /health` prove, and what does it not prove?
- Why must secrets remain outside browser-delivered code?
- What is the difference between linting, static type checking, and tests?
- How does Next.js handle a stopped FastAPI service without crashing?

### What comes next

The next planned milestone was a fixed-seed synthetic Chicago restaurant
dataset with field documentation and quality validation.

## Milestone 1 — Reproducible synthetic restaurant dataset

### Concepts learned

- A fixed seed controls pseudorandom variation so repeated runs remain stable.
- Balanced assignments guarantee category coverage before random shuffling.
- A data dictionary defines field meaning, types, allowed values, and limits.
- Data provenance explains where data came from and how it may be used.
- Quality tests validate both the generator and the committed artifact.

### Features completed

- Typed Python generator with configurable count, seed, and output path.
- Twenty-four fictional Chicago restaurant records in nested JSON.
- Numeric cost, dietary, opening-hour, coordinate, and multi-origin travel data.
- Six dataset tests covering reproducibility, I/O, schema, and quality.
- Shared root pytest configuration that also runs the existing API test.

### Commands used

- `apps/api/.venv/bin/python scripts/generate_demo_data.py`
- `apps/api/.venv/bin/pytest`
- `apps/api/.venv/bin/ruff check scripts tests`
- `apps/api/.venv/bin/mypy --strict scripts tests`
- `shasum -a 256` and `cmp --silent` for byte-level comparison
- `/usr/bin/time -p` for one measured local generator run

### Errors encountered and solved

- A read-only zsh loop used `path` as a variable name, temporarily replacing
  zsh's special executable-search array. Renaming it restored command lookup.
- Root pytest could not import `scripts` because the repository root was not on
  its import path. A root `pyproject.toml` now declares shared test paths and
  Python paths without adding runtime hacks to test files.
- A generated `apps/api/build/` directory was visible during inspection. The
  standard `build/` pattern is now ignored by Git.

### Questions I should now be able to answer

- Why does a fixed seed make test data reproducible?
- Why must synthetic records be labeled clearly?
- What is the difference between a price category and numeric cost?
- Why validate the committed dataset as well as the generator?
- How does data lineage help future pipeline debugging?

### What comes next

Milestone 2 will build a structured FastAPI restaurant-search endpoint over the
synthetic dataset. It must not begin until explicitly approved.

## Milestone 2 — Basic backend restaurant search

### Concepts learned

- Query parameters carry structured filters in a `GET` request URL.
- Pydantic request models validate types and relationships before business
  logic runs; response models validate what the API sends back.
- AND filtering means a record must satisfy every supplied condition.
- A repository abstracts data access, while a service owns business rules and
  a route translates HTTP requests and errors.
- HTTP 200 with an empty list means the request was valid but found no matches;
  HTTP 422 means the request itself was invalid.

### Features completed

- `GET /restaurants/search` with five optional structured filters.
- Case-insensitive cuisine and starting-area normalization.
- Inclusive budget filtering and vegetarian-option filtering.
- Maximum travel filtering using the faster walking or transit estimate.
- Stable typed results, canonical applied filters, and explicit match counts.
- Twelve search tests plus live HTTP and OpenAPI verification.

### Commands used

- `.venv/bin/pytest apps/api/tests/test_restaurant_search.py`
- `.venv/bin/ruff check apps/api/src apps/api/tests`
- `.venv/bin/mypy --strict apps/api/src apps/api/tests`
- `.venv/bin/uvicorn --app-dir apps/api/src bitecheck_api.main:app --port 8001`
- `curl` and `jq` for live contract inspection

### Errors encountered and solved

- A raw Python import initially found the older normal-installed package copy
  instead of `apps/api/src`. Source-aware pytest and Uvicorn checks confirmed
  the new route, and the package was reinstalled after the source changes.
- A quick response probe expected a generic `id` key; the documented dataset
  and API contract correctly use `restaurant_id`.

### What comes next

Milestone 3 will add a basic frontend form that sends these structured filters
to FastAPI and handles loading, success, empty, and error states. It must not
begin until explicitly approved.

## Milestone 3 — Basic frontend search

### Concepts learned

- React state stores changing form values and determines which UI state is
  visible.
- A Client Component is needed for browser event handlers; static surrounding
  content can remain server-rendered.
- A Next.js Route Handler can act as a small backend-for-frontend proxy, keeping
  backend configuration server-only and avoiding browser CORS problems.
- TypeScript describes expected data during development, while a runtime guard
  checks that real JSON actually follows that contract.
- Empty results are a successful search outcome, while unavailable services are
  operational errors that need different user guidance.

### Features completed

- Personalized five-filter search form with editable suggested preferences.
- Same-origin browser-to-Next.js-to-FastAPI request flow.
- Responsive restaurant cards and applied-filter summaries.
- Idle, loading, success, empty, and unavailable-service states.
- Five frontend contract tests with no additional testing dependency.
- Desktop and 390-pixel browser verification with no console errors.

### Commands used

- `npm test`, `npm run lint`, and `npm run build`
- `npm run dev` and FastAPI's local Uvicorn command
- `curl` for the same-origin proxy contract
- In-app browser inspection for form submission and responsive verification

### Errors encountered and solved

- ESLint initially inspected generated CommonJS test output. The disposable
  `.test-dist` directory is now ignored by both Git and ESLint.
- Opening the dev server as `127.0.0.1` blocked Next.js hot-reload resources
  advertised for `localhost`, so React had not attached before the first form
  click. Verification used the documented `http://localhost:3000` address.
- An accessibility-label locator behaved inconsistently for a native select;
  the browser test confirmed the selected value through the element's stable
  `name` attribute.

### What comes next

Milestone 4 will convert natural-language restaurant requests into the same
structured filter shape. It must not begin until explicitly approved.

## Milestone 4 — Rule-based natural-language parser

### Concepts learned

- Normalization creates one stable comparison form for differences in case,
  Unicode width, tabs, newlines, and repeated spaces.
- Keyword matching is appropriate for closed categories such as the ten known
  cuisines and seven supported starting areas.
- Regular expressions extract patterned values such as `$25` and `30 minutes`,
  but units and surrounding words are essential for avoiding false matches.
- A conservative parser reports ambiguity instead of silently choosing a
  meaning the user did not express.
- A protocol separates the parser contract from its rule-based implementation,
  allowing a later AI adapter to return the same filter model.

### Features completed

- Typed `POST /restaurants/parse` endpoint.
- Case, Unicode, and whitespace normalization.
- Cuisine and Chicago-area keyword and alias dictionaries.
- Budget, travel-time, and vegetarian phrase extraction.
- Explicit ambiguity, incomplete-travel, and non-positive-value errors.
- Thirty-eight parser and endpoint tests.

### Commands used

- `.venv/bin/pytest apps/api/tests/test_natural_language_parser.py`
- `.venv/bin/ruff check apps/api/src apps/api/tests`
- `.venv/bin/mypy --strict apps/api/src apps/api/tests`
- `curl` and `jq` for live parse, error, OpenAPI, and search-handoff checks

### Errors encountered and solved

- The first negative vegetarian rule recognized “vegetarian options optional”
  but not “vegetarian options are optional.” The expression now handles the
  linking verb without changing positive matches.
- An ambiguity test wrote one travel number without a unit. Because the parser
  correctly requires `minutes` or `mins`, the test was corrected so both
  competing numbers state their unit.
- Non-positive values initially would have reached Pydantic from inside the
  parser. Explicit rule errors now turn them into controlled HTTP 422 responses.

### What comes next

Milestone 5 will categorize synthetic travel estimates into explainable
walking, public-transit, and driving convenience groups. It must not begin
until explicitly approved.

## Milestone 5 — Transportation categorization

### Concepts learned

- Classification rules turn continuous measurements into named analytical
  groups, but boundary definitions and evaluation order must be explicit.
- Mutually exclusive categories let counts add back to the source population.
- A user limit and a category threshold answer different questions: whether a
  trip is acceptable and what convenience label describes it.
- Parameterized thresholds support scenario analysis without changing code.
- Row-level explanations make aggregate category KPIs auditable.

### Features completed

- Six transportation categories with walking-first priority.
- Configurable, validated thresholds and maximum acceptable time.
- Per-restaurant travel minutes, decision, selected mode, and explanation.
- Aggregate category counts for every response.
- Typed travel-categorization endpoint and 19 focused tests.

### Commands used

- `.venv/bin/pytest apps/api/tests/test_travel_categories.py`
- `.venv/bin/ruff check` and strict `.venv/bin/mypy`
- `curl` and `jq` for live OpenAPI, counts, thresholds, and example inspection

### Errors encountered and solved

- The first smoke probe used the natural-language alias `iit` in a structured
  query. Structured endpoints deliberately use canonical values; the supported
  case-insensitive value `Illinois Tech` succeeded.
- A parametrized test used an overly broad `object` value type that did not
  satisfy the HTTP client's query mapping annotation. Narrowing it to actual
  string and integer query types restored strict type safety.

### What comes next

Milestone 6 adds an explainable restaurant-ranking engine with configurable
factor weights. Per the updated workflow, it starts automatically.

## Milestone 6 — Explainable ranking

Normalized 0–100 factor scores make different units comparable. Effective
weights exclude unavailable and irrelevant factors, and each weighted
contribution reconciles to the displayed total. Review Confidence remains
explicitly unavailable rather than being inferred from rating. Stable shared
ties keep the result deterministic. Twelve focused tests and a live eight-match
ranking verified the model.

## Milestone 7 — Synthetic review data

Unstructured test data needs controlled language variation and deliberately
engineered edge cases. A fixed seed and reference date make text, dates, and
flags reproducible. Exact and near-duplicate lineage, branch foreign keys,
source identities, and burst groups demonstrate data modelling as well as text
generation. Nine focused tests validate the 288 committed records.

The next milestone automatically builds rule-based aspect and sentiment
analysis over these reviews.

## Milestone 8 — Review-theme analysis

Aspect-based sentiment attaches opinion to a subject instead of reducing a
whole review to one label. Clause segmentation lets “food was excellent, but
service was slow” preserve both opinions. Extraction and evaluation are separate
to prevent label leakage. The controlled baseline reached 0.9655 precision,
1.0000 recall, and 0.9825 F1 across 672 expected pairs, with nine focused tests.

The next milestone automatically designs the Review Confidence Score from
source agreement, volume, freshness, duplication, and suspicious activity.

## Milestone 9 — Review Confidence Score

A metric is a documented model of assumptions, not a discovered fact. BiteCheck
normalizes different measurements onto one scale, weights seven supporting
signals, and keeps four penalties separate so the total remains auditable. The
fixed reference date makes freshness reproducible. Cross-source agreement and
rating consistency measure evidence patterns, but neither proves truth.

The analytics artifact now passes through a typed repository before serving.
Every component can be inspected at `GET /restaurants/review-confidence`, while
ranking uses the final score with an explicit evidence-quality explanation.
Focused tests verify determinism, bounds, factor sets, arithmetic
reconciliation, controlled burst penalties, safe failures, and ranking handoff.

The next milestone automatically turns these backend signals into polished,
decision-focused recommendation cards.

## Milestone 10 — Restaurant recommendation interface

A decision interface needs a presentation contract, not a pile of unrelated API
responses. FastAPI now performs the analytical joins and assigns relative
category winners; the browser validates one card-ready response before rendering
it. Removing exact duplicates from theme frequencies demonstrates how data
cleaning changes what a user sees, not only what a pipeline stores.

The cards use visual hierarchy to separate the overall score, practical details,
review strengths, concerns, confidence, explanation, and freshness. Live checks
verified eight suggested results, all eight category definitions, keyboard-
accessible category explanations, an actionable empty state, a three-column
desktop grid, a narrow layout without horizontal overflow, and no browser
console errors.

Milestone 11 will add deterministic conversational follow-up transitions while
keeping the current filter and ranking contracts explicit.

## Milestone 11 — Conversational follow-up searches

Conversation is state plus transitions. The important engineering decision is
not the chat-shaped input; it is making the current filters and preferences
explicit so each turn can be reproduced. BiteCheck sends state with every
request, recognizes one supported intent, returns an explanation, and never
mutates the previous state when a request fails.

Fourteen focused backend tests cover all eight intents, walkable travel
filtering, chained walkable-then-cheapest state, theme and confidence sorting,
missing origin, unsupported language, and reset. The frontend keeps the normal
form synchronized with returned state, so conversational changes remain visible
and editable. No API key or paid model is required.

Milestone 12 will add optional browser speech around the same text contract;
voice will remain progressive enhancement rather than a requirement.

## Showcase release hardening

A public portfolio repository needs more than working feature code. BiteCheck
now has a recruiter-first README, a real result screenshot, continuous
integration, a production backend container, deployment instructions, and
explicit synthetic-data limitations. Dependency auditing also matters: the
Next.js packages were upgraded to patched releases, the production audit is
clean, and the backend test client is now declared directly instead of relying
on an unrelated environment package.

The final local release check passed 142 Python tests and 17 TypeScript tests,
strict Python type checking, both linters, dependency checks, and the Next.js
production build. Hosting remains an account-level action rather than a hidden
part of the codebase.
