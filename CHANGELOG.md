# Changelog

All notable project changes will be recorded here.

## Unreleased

### Added

- Live City of Chicago inspection provider with server-side geographic and text
  queries, external-row validation, license deduplication, and safe timeouts.
- Public inspection explorer with real addresses, current-location or preset
  area search, official-result filters, exact map links, and factual cards.
- Separate primary public-data and synthetic Analytics Lab experiences so demo
  review signals cannot be mistaken for real restaurant claims.
- Browser-only current-location distance and nearest-result ordering, with a
  deliberate permission control and no coordinate transfer to the backend.
- Prominent real-address links to exact OpenStreetMap coordinates.
- Multi-select follow-up actions that replay deterministic state transitions in
  the order selected.
- A more interactive recommendation interface with clearer location, sorting,
  selection, privacy, and responsive-state feedback.
- Reproducible City of Chicago Food Inspections ingestion and cleaning pipeline
  with source attribution, license deduplication, history counts, and a fixed
  24-establishment snapshot.
- Hybrid restaurant schema and UI inspection summaries that distinguish real
  public identity fields from synthetic recommendation enrichment.
- Milestone 0 documentation and repository safety foundation.
- Next.js 16 frontend scaffold with strict TypeScript, the App Router, Tailwind
  CSS, ESLint, and a pinned npm dependency tree.
- Responsive BiteCheck development health page with accurate frontend and
  backend status labels.
- Typed FastAPI backend with a documented `GET /health` response contract.
- Isolated Python environment configuration with Ruff, mypy, pytest, and
  dependency validation.
- Server-rendered Next.js health integration with response-shape validation,
  a two-second timeout, and safe connected and unavailable UI states.
- Fixed-seed Python generator for 24 fictional Chicago restaurant records.
- Versioned nested JSON schema containing cuisine, cost, dietary, rating,
  opening-hour, coordinate, and synthetic transportation fields.
- Root Python tool configuration and six focused dataset tests.
- Typed `GET /restaurants/search` API with five optional, composable filters.
- Validated JSON repository, filtering service, and thin FastAPI route layers.
- Canonical case-insensitive cuisine and starting-area matching.
- Fastest non-driving travel filtering with the selected mode in each result.
- Twelve focused search tests covering success, empty, validation, and
  unavailable-data behavior.
- Personalized structured-search form with suggested Chicago preferences.
- Responsive restaurant cards with cost, dietary, dataset-rating, and travel
  information.
- Same-origin Next.js search route that keeps the backend URL server-only.
- Runtime validation for FastAPI responses before rendering browser results.
- Five TypeScript contract tests using the built-in Node.js test runner.
- Replaceable deterministic restaurant-request parser with versioned rules.
- Unicode, case, and whitespace normalization for natural-language input.
- Keyword dictionaries for ten cuisines, seven starting areas, and aliases.
- Regular-expression extraction for budgets and maximum travel minutes.
- Typed `POST /restaurants/parse` endpoint with explicit ambiguity errors.
- Thirty-eight focused parser and endpoint test cases.
- Configurable transportation thresholds with order validation.
- Deterministic walking, transit, driving, and inconvenient classifications.
- Typed `GET /restaurants/travel-categories` endpoint with category totals and
  per-restaurant explanations.
- Nineteen focused transportation boundary and endpoint tests.
- Versioned weighted-ranking configuration and explainable factor contributions.
- Typed `POST /restaurants/rank` with missing-factor renormalization and stable
  tie behavior, plus twelve focused tests.
- Fixed-seed generator for 288 multi-source fictional review records.
- Ground-truth aspect, sentiment, duplicate, age, and burst labels for review
  pipeline evaluation, plus nine focused data-quality tests.
- Rule-based clause-level extraction for all 15 review themes with evidence.
- Deterministic review-theme analytics output, aggregate sentiment counts, and
  held-apart ground-truth evaluation with nine focused tests.
- Versioned Review Confidence methodology with seven weighted supporting
  components and four capped evidence-quality penalties.
- Deterministic per-restaurant confidence analytics with complete component,
  source, penalty, band, and interpretation detail.
- Validated `GET /restaurants/review-confidence` inspection endpoint and active
  Review Confidence integration in explainable ranking.
- Deterministic recommendation-insight artifact with duplicate-aware positive
  and negative theme summaries plus freshness.
- Typed `POST /restaurants/recommendations` joining ranking, travel, themes,
  confidence, category reasons, and restaurant presentation fields.
- Responsive accessible recommendation cards covering all eight roadmap
  categories with runtime browser-contract validation.
- Explicit conversational state and eight deterministic follow-up intents for
  travel, cost, themes, confidence, complaints, showing all, and reset.
- Typed `POST /restaurants/conversation`, same-origin frontend proxy, and
  accessible follow-up controls with synchronized structured filters.
- GitHub Actions quality gates for Python and TypeScript checks.
- Portable FastAPI container and public deployment instructions.
- Recruiter-focused README and verified application screenshot.
- Optional browser-native voice input and speech controls around the typed
  conversation contract.

### Verified

- Frontend lint, production build, and local HTTP smoke test.
- Frontend health page at desktop and 390-pixel viewport widths with semantic
  content, no horizontal overflow, and no browser console errors.
- Backend import, lint, strict type check, health endpoint test, dependency
  compatibility, and live HTTP smoke test.
- End-to-end health integration with FastAPI available and unavailable.
- Dataset schema, quality, geographic-bound, dietary-consistency, file-output,
  and reproducibility checks.
- Byte-identical JSON output across repeated seed-42 generator runs.
- Live OpenAPI and restaurant-search responses on a temporary local server.
- All five structured filters independently and in combination.
- Safe HTTP 422 and 503 error contracts.
- End-to-end form submission producing eight suggested matches.
- Clear empty-results and unavailable-backend browser states.
- Structured search UI at desktop and 390-pixel widths with no horizontal
  overflow and no browser console errors.
- Full product sentence parsed into all five structured filters.
- Ambiguous cuisine and incomplete travel requests returning HTTP 422.
- Parsed Japanese preferences handed to search and returning two matches.
- All 24 Illinois Tech travel estimates assigned exactly one category.
- Custom user limits, reversed thresholds, unsupported areas, and safe source
  failures verified.
- Ranking factor contributions reconciled to totals without inventing Review
  Confidence data.
- Review dataset linkage, source balance, theme coverage, edge-case quotas, and
  reproducibility verified.
- Review-theme precision, recall, F1, duplicate consistency, and aggregate
  reconciliation verified.
- Review Confidence component and penalty reconciliation, deterministic output,
  artifact validation, safe failure behavior, and ranking integration verified.
- Recommendation joins, category winners, empty and failure states, responsive
  layouts, expandable reasons, and clean browser console verified.
- Multi-turn state preservation, walkable filtering, theme and confidence
  sorting, reset behavior, and conservative unsupported-language errors verified.
- Clean production dependency audit, 159 automated tests, strict mypy, both
  linters, and the Next.js production build after showcase hardening.
