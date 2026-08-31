# Recommendation interface methodology

Milestone 10 turns separate analytical outputs into a decision-focused view.
`POST /restaurants/recommendations` accepts the same filters and optional
weights as ranking, then joins restaurant details, ranking factors, synthetic
travel estimates, review themes, Review Confidence, and freshness.

## Data flow

```text
User filters
  -> filter and explainable rank
  -> join restaurant + confidence + card-ready review insights
  -> calculate travel presentation and category winners
  -> typed recommendation response
  -> server-side Next.js proxy
  -> runtime TypeScript validation
  -> accessible responsive cards
```

The card-ready insight build excludes 24 exact-duplicate reviews before theme
counts so copied text does not inflate the displayed recurring themes. It keeps
the three most frequent positive and negative themes per restaurant, breaking
ties alphabetically. Observation count and freshness still describe the full
source review set.

## Recommendation categories

Categories describe one winner within the current filtered result set. A
restaurant may win more than one category, and categories without an eligible
candidate are omitted.

| Category | Rule |
| --- | --- |
| Best overall | First restaurant in weighted ranking |
| Best walkable | Highest-ranked result whose selected category uses walking |
| Best by public transportation | Highest-ranked result whose transit estimate fits the user's limit, or 50 minutes by default |
| Best value | Lowest estimated cost; weighted score breaks a cost tie |
| Most consistently recommended | Highest Review Confidence; weighted score breaks a tie |
| Best vegetarian match | Highest-ranked result with vegetarian availability |
| Hidden gem | Highest-ranked result with rating at least 4.0, confidence at least 65, and dataset rating count at or below the result-set median |
| Mixed reviews — proceed carefully | Lowest rating-consistency component when that component is below 60 |

Every winning badge includes a plain-language reason. These are deterministic
product definitions, not universal definitions of value, quality, or a hidden
gem.

## Card content and states

Each card displays rank, total score, price, dataset rating, dietary options,
all three travel estimates when an origin is supplied, top positive and
negative themes, Review Confidence, ranking explanation, category reasons, and
latest synthetic review date. The interface handles idle, loading, ranked,
empty, and unavailable-service states. Result focus and `aria-live` announce
asynchronous outcomes, native labels remain associated with controls, and
category explanations use keyboard-accessible `details` elements.

## Limitations

- All current content and measurements are synthetic.
- Theme frequency does not measure importance to every user.
- Exact duplicates are removed from card theme counts, but near-duplicates
  remain and may still influence displayed frequency.
- Category rules select relative winners from the current result set; a badge
  does not imply an absolute quality threshold unless the rule states one.
- Public-transit and walking minutes are synthetic estimates, not directions.
- The interface does not yet remember or reinterpret follow-up requests; that
  is Milestone 11.
