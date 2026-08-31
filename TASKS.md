# BiteCheck tasks

## Milestone 0 — Development environment and architecture

- [x] Inspect the existing workspace.
- [x] Agree on the initial architecture and project location.
- [x] Create the documentation and safety foundation.
- [x] Install and verify a maintained Node.js LTS release.
- [x] Scaffold and verify the Next.js frontend.
- [x] Scaffold and verify the FastAPI backend.
- [x] Add and verify the static frontend health page.
- [x] Add and verify the backend health endpoint.
- [x] Add focused tests.
- [x] Connect the frontend health page to the backend.
- [x] Complete Milestone 0 documentation and verification.

## Milestone 1 — Reproducible synthetic restaurant dataset

- [x] Define the restaurant dataset schema and allowed values.
- [x] Implement a fixed-seed Python generator.
- [x] Generate 24 clearly labeled synthetic Chicago restaurants.
- [x] Add automated schema, quality, and reproducibility tests.
- [x] Verify byte-identical output for repeated runs with the same seed.
- [x] Document fields, lineage, decisions, limitations, and measured results.

## Milestone 2 — Basic backend restaurant search

- [x] Define strict request and response models.
- [x] Add a replaceable repository interface for the synthetic JSON dataset.
- [x] Implement cuisine, budget, vegetarian, starting-area, and travel filters.
- [x] Return canonical applied filters and stable, typed restaurant results.
- [x] Add clear 422 validation errors and a safe 503 data-source error.
- [x] Add focused API contract and filtering tests.
- [x] Verify the route through a live FastAPI process.
- [x] Document the endpoint, data flow, decisions, and measured results.

## Milestone 3 — Basic frontend search

- [x] Define typed frontend request and response contracts.
- [x] Add a same-origin Next.js route handler that forwards searches to FastAPI.
- [x] Build a personalized structured-filter form with suggested preferences.
- [x] Display responsive restaurant cards and applied-filter summaries.
- [x] Handle idle, loading, success, no-match, and unavailable-service states.
- [x] Add five TypeScript contract tests using Node's built-in test runner.
- [x] Verify desktop and 390-pixel layouts in a real browser.
- [x] Verify successful, empty, and unavailable-service interactions.
- [x] Document the frontend data flow, decisions, and measured results.

## Milestone 4 — Rule-based natural-language parser

- [x] Define a replaceable sentence-to-filter parser interface.
- [x] Normalize case, Unicode, and whitespace deterministically.
- [x] Match all supported cuisines, starting areas, and useful aliases.
- [x] Extract budgets and travel minutes without confusing their units.
- [x] Recognize positive and negative vegetarian wording conservatively.
- [x] Reject ambiguous, incomplete, and non-positive constraints clearly.
- [x] Expose typed `POST /restaurants/parse` request and response contracts.
- [x] Add 38 focused parser and endpoint test cases.
- [x] Verify live parsing, error behavior, and parsed-filter search handoff.
- [x] Document rules, limitations, decisions, and measured results.

## Milestone 5 — Transportation categorization

- [x] Define six mutually exclusive travel-convenience categories.
- [x] Implement walking-first, transit-second, driving-third priority rules.
- [x] Add configurable thresholds and a maximum acceptable user time.
- [x] Validate threshold ordering and positive values.
- [x] Return travel minutes, selected mode, category, and explanation.
- [x] Add category counts for analytics use.
- [x] Expose typed `GET /restaurants/travel-categories`.
- [x] Add 19 boundary, service, and endpoint tests.
- [x] Verify all 24 records are categorized exactly once.
- [x] Document definitions, decisions, limitations, and measured results.

Milestone progression now continues automatically until user input is required.

## Milestone 6 — Explainable restaurant ranking

- [x] Store validated default weights in versioned JSON configuration.
- [x] Normalize cuisine, dietary, budget, travel, and rating factors.
- [x] Mark missing Review Confidence unavailable without inventing data.
- [x] Renormalize active weights and reconcile factor contributions.
- [x] Implement deterministic descending order and shared tie ranks.
- [x] Expose typed `POST /restaurants/rank` with custom weights.
- [x] Add 12 focused ranking and configuration tests.
- [x] Document formulas, missing-data behavior, and limitations.

## Milestone 7 — Synthetic review data

- [x] Define a branch-linked multi-source review schema.
- [x] Generate 288 reviews with a fixed seed and reference date.
- [x] Cover positive, negative, and mixed sentiment.
- [x] Guarantee exact duplicates, near-duplicates, old reviews, and bursts.
- [x] Add expected aspect labels covering all 15 Milestone 8 themes.
- [x] Add nine reproducibility, linkage, schema, and edge-case tests.
- [x] Document fields, lineage, bias, limitations, and measured quotas.

## Milestone 8 — Review-theme analysis

- [x] Define transparent vocabularies for all 15 roadmap themes.
- [x] Normalize review text and split contrastive clauses.
- [x] Extract review-level aspect sentiment with evidence text.
- [x] Produce theme and sentiment aggregate counts.
- [x] Evaluate predictions only after extraction against separate ground truth.
- [x] Generate deterministic `data/analytics/review_themes.json`.
- [x] Add nine focused extraction, reconciliation, and evaluation tests.
- [x] Document methodology, bias, and synthetic-baseline limitations.

## Milestone 9 — Review Confidence Score

- [x] Store versioned component weights, targets, penalties, and score bands.
- [x] Normalize seven evidence-supporting components to 0–100.
- [x] Apply exact-duplicate, repetitive-language, burst, and missing-data penalties.
- [x] Preserve every score, contribution, penalty, and explanation.
- [x] Generate deterministic `data/analytics/review_confidence.json`.
- [x] Add a validated repository and typed inspection endpoint.
- [x] Activate Review Confidence in the explainable ranking engine.
- [x] Add focused calculation, validation, API, and integration tests.
- [x] Document formulas, assumptions, missing-data behavior, bias, and limits.

## Milestone 10 — Restaurant recommendation interface

- [x] Combine ranking, review themes, confidence, and freshness in one API view.
- [x] Assign all eight explainable recommendation categories when eligible.
- [x] Build polished, accessible, responsive recommendation cards.
- [x] Show positive/negative themes, travel, confidence, and ranking reasons.
- [x] Exclude exact duplicates from displayed theme-frequency insights.
- [x] Validate combined responses at both FastAPI and browser boundaries.
- [x] Test data contracts, categories, UI states, and responsive behavior.

## Milestone 11 — Conversational follow-up searches

- [x] Define explicit conversation state and eight supported follow-up intents.
- [x] Apply deterministic filter, travel, theme, sort, and limit transitions.
- [x] Carry state safely across multi-turn sequences without a server session.
- [x] Reject unsupported language and missing travel context instead of guessing.
- [x] Add a conversational request UI without requiring a paid model.
- [x] Keep the structured form synchronized with returned conversation state.
- [x] Add focused intent, state-transition, sequence, and error tests.

## Milestone 12 — Browser voice input and output

- [x] Add optional push-to-talk speech recognition with editable transcript.
- [x] Keep complete text input fallback and unsupported-browser guidance.
- [x] Add browser speech synthesis, stop control, and off-by-default preference.
- [x] Handle recognition, permission, no-speech, and unsupported states.
- [x] Add four focused voice-adapter tests and pass production build checks.

### Optional device verification (not release-blocking)

- [ ] Repeat the live microphone permission check on each browser/device that a
  future deployment chooses to support. Text input remains the complete fallback.

## Maintenance backlog

- [x] Upgrade to patched Next.js packages and pass the production dependency
  audit with zero reported vulnerabilities.
- [x] Add GitHub Actions, portable deployment files, and a public-project README.
