# Architecture

## Milestone 0

```text
Browser
  -> Next.js frontend (`apps/web`)
  -> server-side HTTP/JSON request
  -> FastAPI backend (`apps/api`)
  -> validated JSON response
  -> Next.js renders connected or unavailable status
```

The frontend owns presentation and browser interaction. The backend owns
validation, business logic, server-only configuration, and—later—data access.
Keeping these responsibilities separate prevents secrets from being shipped to
the browser and lets each application be tested independently.

The implemented backend health contract is:

```http
GET /health
```

```json
{"status": "ok", "service": "bitecheck-api"}
```

No database, restaurant provider, review provider, or voice provider is part of
Milestone 0.

## Milestone 2 restaurant search

```text
HTTP query parameters
  -> Pydantic request validation
  -> FastAPI route
  -> RestaurantSearchService
  -> RestaurantRepository interface
  -> validated synthetic JSON adapter
  -> stable filtering in dataset order
  -> Pydantic response validation
  -> JSON response
```

The route translates HTTP input and errors. The service owns filtering rules.
The repository owns file access and dataset validation. This separation keeps
the filter logic testable and allows a later PostgreSQL repository to replace
JSON without changing the public endpoint.

`GET /restaurants/search` supports cuisine, maximum budget, vegetarian
requirement, starting area, and maximum travel time. The route does not parse
natural language, rank results, or access a database.

## Failure behavior

The Next.js server waits at most two seconds for `GET /health`. A connection
failure, non-2xx response, invalid JSON, or unexpected response shape becomes a
safe `unavailable` UI state. Technical error details are not sent to the user.

Restaurant request-shape errors and unsupported category values return HTTP
422. A missing or invalid dataset returns HTTP 503 with a generic message.

## Milestone 3 frontend search

```text
Structured browser form (Client Component)
  -> typed frontend query builder
  -> GET /api/restaurants/search (Next.js Route Handler)
  -> server-only API_BASE_URL
  -> GET /restaurants/search (FastAPI)
  -> runtime response-shape validation
  -> loading, cards, empty, or error UI
```

The interactive form is a focused Client Component because it needs React
state and event handlers. The surrounding page remains a Server Component and
still checks backend health without sending configuration to the browser.

The Next.js Route Handler is a small backend-for-frontend boundary. The browser
calls the same origin, so local CORS configuration is unnecessary, and the
FastAPI location remains a server-only runtime value. The browser client also
checks the response shape before trusting it as restaurant data.

## Milestone 4 natural-language parsing

```text
POST /restaurants/parse with a sentence
  -> Pydantic body validation
  -> Unicode, case, and whitespace normalization
  -> cuisine and starting-area keyword dictionaries
  -> budget and travel-time regular expressions
  -> ambiguity and completeness checks
  -> existing RestaurantSearchFilters model
  -> structured JSON
```

`RestaurantRequestParser` is a protocol, and
`RuleBasedRestaurantRequestParser` is its first adapter. The route depends on
the protocol rather than constructing parsing rules itself. A future AI parser
can therefore produce the same `RestaurantSearchFilters` contract without
changing search logic.

Parsing and searching remain separate operations. The parser translates words;
the search service applies the translated filters to restaurant records. This
separation makes each stage independently testable and prevents language rules
from leaking into data access.

## Milestone 5 transportation categorization

```text
Starting area + configurable thresholds
  -> validated synthetic travel estimates
  -> maximum acceptable time check per mode
  -> walking rules
  -> public-transit rules
  -> driving rule
  -> inconvenient fallback
  -> per-restaurant decision + aggregate category counts
```

The categorizer produces one mutually exclusive primary category per
restaurant. Priority is walking, transit, then driving so a short walk is not
hidden by a faster drive. Thresholds are explicit API inputs with roadmap
defaults and relationship validation. Category counts provide an analytics-ready
summary while item explanations preserve row-level traceability.

## Milestone 6 explainable ranking

```text
Filters -> matching restaurants -> factor normalization
        -> active-weight renormalization -> contributions
        -> total score -> stable descending order + shared ties
```

Default weights are data in `config/ranking_weights.json`, not constants hidden
inside ranking code. Every output factor exposes status, score, configured and
effective weight, contribution, and explanation. Review Confidence is an
unavailable factor until its own milestone and is never synthesized from rating.

## Milestone 7 review generation

```text
Restaurant branches + fixed seed + fixed reference date + text blueprints
  -> 288 raw-looking synthetic reviews
  -> controlled exact/near duplicates, old records, and burst groups
  -> expected aspect and sentiment ground truth
  -> data/synthetic/reviews.json
```

Review IDs and source IDs are unique, while `restaurant_id`, branch name, and
address preserve entity linkage. Edge-case flags are evaluation truth for later
pipelines, not claims that a production detector already exists.

## Milestone 8 review-theme analytics

```text
Raw review text -> normalization -> clause segmentation
                -> theme vocabulary matching -> local sentiment
                -> evidence-bearing review predictions -> aggregates
Ground truth ------------------------------------------------> evaluation only
```

The extraction path does not read expected labels. Evaluation joins predictions
to ground truth afterward by review, theme, and sentiment. This separation
prevents label leakage and makes the rule baseline replaceable.

## Milestone 9 Review Confidence

```text
Reviews + restaurants + theme analytics + versioned confidence config
  -> deterministic batch scorer
  -> data/analytics/review_confidence.json
  -> validating JSON repository
  -> GET /restaurants/review-confidence
  -> Review Confidence factor in POST /restaurants/rank
```

The batch scorer owns formulas and analytical assumptions. Pydantic serving
models and the repository reject malformed, incomplete, duplicate-ID, or
metadata-inconsistent artifacts. The inspection endpoint exposes every
component and penalty. Ranking consumes only the final score while preserving
its evidence-quality explanation; it does not reinterpret review ratings as a
confidence proxy.

## Milestone 10 recommendation interface

```text
POST /restaurants/recommendations
  -> ranking service
  -> restaurant + confidence + recommendation-insight repositories
  -> category assignment and card response
  -> POST /api/restaurants/recommendations (Next.js server proxy)
  -> runtime response validation
  -> interactive recommendation cards
```

The combined endpoint prevents the browser from coordinating several analytics
requests or rebuilding business rules. FastAPI owns joins and category
definitions; Next.js keeps the backend location server-only; the Client
Component owns form state, focus management, and presentation.

## Milestone 11 conversational follow-ups

```text
Follow-up input + explicit client state
  -> POST /api/restaurants/conversation
  -> POST /restaurants/conversation
  -> deterministic intent transition
  -> existing recommendation service
  -> conversational post-filter or sort
  -> updated state + explanation + cards
```

No server session is required. State travels in the typed request and response,
which makes transitions replayable and prevents hidden conversational memory.
The existing recommendation service remains the source of card data.
