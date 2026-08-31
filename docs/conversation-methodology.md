# Conversational follow-up methodology

Milestone 11 remembers explicit search state and applies a small set of free,
deterministic follow-up rules. It does not call a language model and does not
hide state inside a server session or browser cookie.

## State and data flow

```text
Follow-up text + current state
  -> normalize text
  -> choose exactly one supported intent or return HTTP 422
  -> copy and update filters, travel preference, theme preference,
     sort mode, and result limit
  -> rebuild recommendations from source analytics
  -> apply conversational filtering/sorting
  -> return updated state + transition explanation + cards
```

The client sends the current state with every request and replaces it only after
a successful response. This makes every transition inspectable, replayable, and
easy to regression test.

The interface may select several supported suggestions at once. It submits them
one at a time in selection order, carrying each successful returned state into
the next request. This composes the same tested single-intent transitions instead
of creating a second hidden rules engine in the browser. If one request fails,
the sequence stops and reports the error.

## Supported intents

| Example | State transition |
| --- | --- |
| Only show walkable options | Keep only cards whose selected travel mode is walking; requires a starting area |
| Show me the cheapest one | Sort by estimated cost and keep one result |
| Which has better vegetarian choices? | Require vegetarian availability and prioritize positive `vegetarian_options` mentions |
| Prioritize authenticity over distance | Prioritize positive `authenticity` mentions; weighted score breaks ties |
| Which has the most reliable reviews? | Sort by Review Confidence and keep one result |
| What are the common complaints? | Preserve matches and surface their negative theme lists |
| Show all options | Clear conversational sorting, theme, travel, and limit preferences |
| Start over | Reset both structured filters and conversational preferences |

The service returns the recognized intent, updated state, a plain-language
transition explanation, the candidate count before any one-result limit, and a
complete recommendation response.

## Failure behavior and limitations

- Unknown requests return HTTP 422 with supported examples; the parser does not
  silently guess.
- Walkable filtering without a starting area returns HTTP 422.
- Keyword rules cover only the documented English phrasing and close variants.
- Theme priority uses positive mention counts from synthetic rule-based
  analysis. Equal theme counts fall back to the weighted ranking.
- “Open now,” multi-city requests, arbitrary cuisines, and unsupported free-form
  preference combinations remain unavailable. Multiple visible supported
  actions can be stacked in the interface.
- Conversation state belongs to the current browser interaction and is not
  stored in a database or associated with a user identity.
