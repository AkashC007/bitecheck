# Project decisions

## PD-001: Isolate BiteCheck from neighboring portfolio projects

- **Status:** Accepted
- **Decision:** Build BiteCheck inside its own `bitecheck/` directory.
- **Reason:** The workspace already contains unrelated portfolio projects.
  Isolation reduces accidental edits and gives BiteCheck a clear boundary.

## PD-002: Separate the frontend and backend

- **Status:** Accepted
- **Decision:** Use Next.js for the frontend and FastAPI for the backend.
- **Reason:** Browser concerns remain separate from validation, business logic,
  secrets, and future data access.

## PD-003: Keep secrets on the backend

- **Status:** Accepted
- **Decision:** Real secrets use ignored local environment files or deployment
  secret stores. Only safe placeholders belong in `.env.example`.
- **Reason:** Browser-delivered code can be inspected and must not contain
  credentials.

## PD-004: Pin a maintained Node.js LTS release

- **Status:** Accepted
- **Decision:** Use Node.js 24.18.0 LTS for the Milestone 0 frontend.
- **Reason:** An LTS runtime favors stability and security updates. Recording
  the exact version in `.node-version` makes local and future deployment
  environments easier to reproduce.

## PD-005: Use the Next.js App Router with strict TypeScript

- **Status:** Accepted
- **Decision:** Scaffold `apps/web` with the App Router, a `src/` directory,
  strict TypeScript, Tailwind CSS, ESLint, and npm.
- **Reason:** These defaults provide typed components, clear source boundaries,
  repeatable dependency installation, and automated source checks without
  adding application-specific complexity.

## PD-006: Do not apply a breaking forced audit fix

- **Status:** Accepted; review when a compatible stable patch is available
- **Decision:** Keep the scaffolded Next.js 16.2.10 dependency tree and track
  the two moderate PostCSS audit findings instead of running
  `npm audit fix --force`.
- **Reason:** npm's proposed forced resolution would downgrade Next.js to
  9.3.3, which is a breaking architectural regression. The current starter
  page does not accept or stringify untrusted user CSS, and lint, build, and
  HTTP smoke checks pass.

## PD-007: Use an explicit Python `src` layout

- **Status:** Accepted
- **Decision:** Keep backend source in `apps/api/src/bitecheck_api`, configure
  pytest with `pythonpath = ["src"]`, and start Uvicorn with `--app-dir src`.
- **Reason:** The `src` layout separates importable code from configuration and
  tests. Explicit source paths also avoid relying on editable `.pth` processing,
  which Python 3.14 skipped when macOS marked the generated file as hidden.

## PD-008: Model API responses explicitly

- **Status:** Accepted
- **Decision:** Define the health response with a Pydantic model and declare it
  as the FastAPI route's `response_model`.
- **Reason:** A typed response contract validates output, generates accurate API
  documentation, and gives future frontend code a stable data shape.

## PD-009: Check backend health from a Next.js Server Component

- **Status:** Accepted
- **Decision:** Fetch FastAPI health from the Next.js server using the
  server-only `API_BASE_URL` variable, validate the JSON shape, and fall back to
  an unavailable state after two seconds.
- **Reason:** This completes frontend-to-backend communication without exposing
  configuration in browser JavaScript or adding CORS before it is needed.

## PD-010: Start with synthetic restaurant data

- **Status:** Accepted
- **Decision:** Build the first dataset from transparent local rules and label
  every record synthetic.
- **Reason:** Synthetic data is free, reproducible, legally safer than restricted
  scraping, and lets tests cover edge cases before external-provider variability
  is introduced.

## PD-011: Use nested JSON for the first dataset

- **Status:** Accepted
- **Decision:** Store metadata and restaurant records in one JSON document.
- **Reason:** Opening hours and transportation estimates are naturally nested.
  JSON preserves those relationships without encoding objects inside CSV cells.

## PD-012: Make generation byte-reproducible

- **Status:** Accepted
- **Decision:** Use a local `random.Random` instance with seed 42, stable key
  sorting, stable indentation, and no generation timestamp.
- **Reason:** Repeated runs can be compared exactly, which makes tests, reviews,
  and future pipeline changes easier to audit.

## PD-013: Include numeric cost and multi-origin travel estimates

- **Status:** Accepted
- **Decision:** Store an estimated cost per person and synthetic travel values
  from all seven initial starting areas.
- **Reason:** Milestone 2 requires budget, starting-area, and travel-time filters.
  Explicit values avoid reverse-engineering those filters from coarse labels.

## PD-014: Use one typed query model for structured search

- **Status:** Accepted
- **Decision:** Represent all five optional query filters with one strict
  Pydantic model and reject unknown query parameters.
- **Reason:** One request contract keeps validation rules and generated OpenAPI
  documentation synchronized while catching misspelled filters early.

## PD-015: Separate route, service, and repository responsibilities

- **Status:** Accepted
- **Decision:** Keep HTTP translation in the FastAPI router, filtering in a
  service, and JSON access behind a repository protocol.
- **Reason:** The service can be tested independently, errors remain safe at the
  API boundary, and a future database adapter can replace JSON without changing
  the endpoint contract.

## PD-016: Filter travel by the fastest non-driving mode

- **Status:** Accepted
- **Decision:** For the basic maximum-travel-time filter, compare walking and
  public-transit estimates and use the faster value; choose walking on a tie.
- **Reason:** The product example asks for travel by walking or public
  transportation. Driving is intentionally excluded, and explicit tie behavior
  keeps results deterministic. Full transportation categories remain Milestone
  5 work.

## PD-017: Preserve source order instead of ranking search results

- **Status:** Accepted
- **Decision:** Return matching restaurants in their stable dataset order.
- **Reason:** Milestone 2 is filtering only. Ranking now would mix in Milestone
  6 scope and make the basic search contract harder to reason about.

## PD-018: Keep the interactive boundary focused

- **Status:** Accepted
- **Decision:** Keep the page and health check server-rendered while placing
  form state, submission, and result rendering in one Client Component.
- **Reason:** Browser event handlers require a Client Component, but the entire
  page does not. A focused boundary limits browser JavaScript and preserves
  server-only access to runtime configuration.

## PD-019: Proxy browser searches through Next.js

- **Status:** Accepted
- **Decision:** Send browser requests to a same-origin Next.js Route Handler,
  which forwards the query to FastAPI using server-only `API_BASE_URL`.
- **Reason:** This avoids local CORS complexity, keeps backend configuration out
  of the browser bundle, and creates a safe place for future server-side
  provider credentials without adding any credentials now.

## PD-020: Validate API responses at both application boundaries

- **Status:** Accepted
- **Decision:** Keep Pydantic response validation in FastAPI and add a runtime
  TypeScript shape check before the frontend renders a search response.
- **Reason:** TypeScript types disappear at runtime. The browser must not assume
  an HTTP response is trustworthy merely because local source code declares a
  matching type.

## PD-021: Personalize with editable suggested preferences

- **Status:** Accepted
- **Decision:** Prefill budget, vegetarian, Illinois Tech, and travel-time
  preferences while leaving cuisine open, and provide a one-click clear action.
- **Reason:** The screen feels useful on first load and reflects the product
  example, while every preference remains transparent and user-controlled.

## PD-022: Start natural-language parsing with deterministic rules

- **Status:** Accepted
- **Decision:** Use versioned keyword dictionaries and regular expressions for
  the five existing search filters before introducing an AI model.
- **Reason:** Rules are free, fast, reproducible, easy to unit test, and make
  every supported interpretation visible. Their limitations also create a
  measurable baseline for evaluating a later AI parser.

## PD-023: Reuse the search-filter model as parser output

- **Status:** Accepted
- **Decision:** Accept text through `POST /restaurants/parse` and return the
  existing `RestaurantSearchFilters` response shape.
- **Reason:** Parsed output can flow directly into search without another
  translation layer. Pydantic also applies the same positive-number and
  travel-area relationship rules at both entry points.

## PD-024: Reject ambiguity instead of guessing

- **Status:** Accepted
- **Decision:** Return HTTP 422 when text contains multiple values for one
  filter or a travel limit without a starting area. Leave unsupported concepts
  unparsed rather than mapping them to weaker requirements.
- **Reason:** A deterministic but incorrect interpretation is worse than an
  explicit limitation. In particular, a vegan request must not become merely
  vegetarian, and two cuisines must not be reduced to whichever rule runs
  first.

## PD-025: Assign one prioritized travel category

- **Status:** Accepted
- **Decision:** Evaluate walkable, comfortable walk, easy transit, longer
  transit, easy drive, and inconvenient in that order.
- **Reason:** Mutually exclusive output supports clear cards and category KPIs.
  Walking-first priority reflects the product's accessibility focus and avoids
  labeling a walkable restaurant primarily as drivable.

## PD-026: Make transportation definitions configurable

- **Status:** Accepted
- **Decision:** Expose positive, ordered category thresholds plus a maximum
  acceptable user time, while retaining the roadmap values as defaults.
- **Reason:** Business definitions often change. Parameters make scenario
  analysis possible without code edits, while validation prevents overlapping
  ranges from becoming internally inconsistent.

## PD-027: Renormalize ranking weights around available factors

- **Status:** Accepted
- **Decision:** Score active factors on 0–100, exclude not-applicable or
  unavailable factors, and redistribute their configured weight proportionally.
- **Reason:** Missing Review Confidence must not become a fabricated neutral or
  perfect value. Contributions remain comparable and reconcile to the total.

## PD-028: Use stable shared-rank ties

- **Status:** Accepted
- **Decision:** Sort displayed totals descending, assign the same rank to equal
  totals, and retain source order within ties.
- **Reason:** Deterministic ties make tests and explanations reproducible without
  inventing a hidden tie-break preference.

## PD-029: Generate review edge cases by quota

- **Status:** Accepted
- **Decision:** Produce 12 reviews per branch with guaranteed duplicate, near-
  duplicate, old, mixed-sentiment, and burst cases across three fictional sources.
- **Reason:** Randomly hoping for rare cases gives weak test coverage. Controlled
  labels create known answers for later cleaning and analysis evaluation.

## PD-030: Use a fixed review reference date

- **Status:** Accepted
- **Decision:** Anchor review dates to 2026-01-15 and omit generation timestamps.
- **Reason:** “Old” remains objectively testable and repeated generation stays
  byte-reproducible instead of changing with the wall clock.

## PD-031: Keep review ground truth out of extraction

- **Status:** Accepted
- **Decision:** Analyze only raw text, then evaluate predictions against labels
  in a separate step.
- **Reason:** Reading labels during extraction would leak the answer key and
  produce meaningless performance metrics.

## PD-032: Establish a transparent rule baseline before advanced NLP

- **Status:** Accepted
- **Decision:** Use clause segmentation, visible theme vocabularies, and local
  positive/negative terms with evidence text.
- **Reason:** The method is free, deterministic, explainable, and measurable.
  Its known errors form a baseline for judging later NLP improvements.

## PD-033: Separate evidence support from evidence penalties

- **Status:** Accepted
- **Decision:** Build the confidence base from seven normalized supporting
  components, then subtract four independently visible capped penalties.
- **Reason:** Users and analysts can see whether a score changed because of
  weak coverage, inconsistency, staleness, duplication, missingness, or bursts
  instead of treating one opaque number as self-explanatory.

## PD-034: Keep confidence assumptions versioned and reproducible

- **Status:** Accepted
- **Decision:** Store weights, targets, caps, and bands in JSON and use the
  review dataset's fixed 2026-01-15 reference date.
- **Reason:** Analytical assumptions can be reviewed without searching code,
  and recency calculations remain deterministic across repeated runs.

## PD-035: Validate confidence at the serving boundary

- **Status:** Accepted
- **Decision:** Serve confidence through a repository protocol that validates
  the full artifact, expected factor sets, unique IDs, and metadata counts.
- **Reason:** Ranking should consume a trusted analytics contract and return a
  safe error rather than silently using partial or malformed data.

## PD-036: Build one card-ready backend contract

- **Status:** Accepted
- **Decision:** Join ranking, records, travel, themes, confidence, and freshness
  in `POST /restaurants/recommendations` instead of making the browser call and
  combine several endpoints.
- **Reason:** Business definitions remain centralized and typed, the frontend
  receives one consistent snapshot, and failure behavior stays predictable.

## PD-037: Treat recommendation categories as relative explanations

- **Status:** Accepted
- **Decision:** Assign one winner per eligible category within the filtered
  result set and allow a restaurant to win multiple categories.
- **Reason:** The badges answer distinct decision questions without forcing an
  arbitrary exclusive label or pretending every category has a valid candidate.

## PD-038: Remove exact copies from card theme frequencies

- **Status:** Accepted
- **Decision:** Exclude reviews labeled as exact duplicates when building the
  positive and negative theme lists, while preserving full observation counts.
- **Reason:** Copied text should not make a theme appear more recurrent, and
  retaining the source count keeps freshness and coverage descriptions honest.

## PD-039: Keep conversation state explicit and client-carried

- **Status:** Accepted
- **Decision:** Send filters, sorting, travel, theme, and limit preferences with
  every follow-up instead of storing an opaque server session.
- **Reason:** Transitions can be inspected, replayed, tested, and reset without
  user accounts, cookies, or hidden state.

## PD-040: Start follow-ups with conservative deterministic intents

- **Status:** Accepted
- **Decision:** Recognize eight documented intent families and reject unknown
  language with examples rather than guessing.
- **Reason:** Free keyword rules are transparent and measurable. Explicit limits
  are safer than claiming broad conversational understanding.

## PD-041: Reuse analytical outputs for conversational priorities

- **Status:** Accepted
- **Decision:** Sort theme requests by positive theme counts and reliability
  requests by Review Confidence, using weighted score as a stable tie-breaker.
- **Reason:** Follow-ups should reuse documented metrics rather than introduce
  invisible scoring formulas.

## PD-042: Keep the showcase deployment portable

- **Status:** Accepted
- **Decision:** Package FastAPI in a repository-root Dockerfile, keep the
  Next.js deployment standard, and connect them with one server-only URL.
- **Reason:** A portfolio reviewer can run or host the project without a paid
  provider, provider-specific manifest, browser-visible backend configuration,
  or secret API key.

## PD-043: Use public identities with synthetic recommendation enrichment

- **Status:** Accepted
- **Decision:** Replace fictional restaurant identities with a fixed,
  reproducible City of Chicago Food Inspections snapshot while retaining the
  existing synthetic cuisine, price, dietary, rating, review, hours, and travel
  signals.
- **Reason:** This demonstrates real ingestion, cleaning, deduplication, and
  lineage without scraping commercial reviews or making unsupported claims
  about real establishments. Every field group is visibly labeled by origin,
  and inspection results are described as point-in-time observations.

## PD-044: Keep optional current location entirely in the browser

- **Status:** Accepted
- **Decision:** Request geolocation only from a visible user action, retain it
  only in in-memory frontend state, and calculate straight-line distance locally.
- **Reason:** The interface can answer “how far from me?” without creating a
  precise-location backend record. The UI distinguishes this calculation from
  synthetic travel times and from a complete nearby-business search.

## PD-045: Compose multiple follow-ups from single-intent transitions

- **Status:** Accepted
- **Decision:** Apply selected suggestions sequentially in selection order,
  passing each returned state into the next existing conversation request.
- **Reason:** Multi-action behavior stays deterministic, inspectable, and
  covered by the same backend rules instead of duplicating them in the client.
