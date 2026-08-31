# Review Confidence methodology

Review Confidence estimates how strong and internally consistent the available
review evidence is for a restaurant branch. It is not a truth, authenticity,
fraud, or restaurant-quality score. A high score means the current synthetic
evidence meets more of this methodology's reliability assumptions.

## Data flow

```text
Synthetic reviews + branch records + extracted review themes
  -> seven normalized supporting components
  -> weighted base score
  -> four evidence-quality penalties
  -> bounded 0–100 Review Confidence Score + band + explanations
  -> validated analytics API and restaurant ranking factor
```

The fixed reference date is 2026-01-15, matching the synthetic review
generator. Configuration lives in `config/review_confidence.json`; calculated
rows live in `data/analytics/review_confidence.json`.

## Supporting components

Each component is normalized to 0–100. Contribution equals component score
multiplied by its weight. The weights sum to 100%.

| Component | Weight | Current calculation |
| --- | ---: | --- |
| Cross-source agreement | 20% | `100 × (1 - population SD of source mean ratings / 2)`, clamped |
| Observation volume | 10% | `100 × review count / 20`, clamped |
| Review recency | 15% | Mean of `100 × (1 - age days / 730)`, each review clamped |
| Source diversity | 10% | `100 × distinct sources / 3`, clamped |
| Review specificity | 10% | Mean of `100 × extracted theme count / 2`, each review clamped |
| Branch-match confidence | 10% | Percentage matching the restaurant name and address |
| Rating consistency | 25% | `100 × (1 - population SD of review ratings / 2)`, clamped |

The base score is the sum of the seven weighted contributions. A dispersion of
two rating points maps agreement or consistency to zero. Twenty observations,
three sources, two themes per review, and reviews no older than 730 days are
explicit analytical targets, not universal standards.

## Penalties

Each penalty is its affected-observation rate multiplied by a configured cap:

- Exact duplicates: up to 10 points.
- Repetitive or near-duplicate language: up to 5 points.
- Suspicious short-window bursts: up to 10 points.
- Missing required review fields: up to 10 points.

`final score = clamp(base score - total penalties, 0, 100)`

Bands are high at 75 or above, medium at 50–74.99, and low below 50. Every API
row exposes raw component scores, weights, contributions, penalty rates, caps,
deductions, source counts and means, the base score, and the final score.

## Missing data behavior

Missing values reduce the score through a visible penalty; they are not silently
filled with an average. A missing or invalid analytics artifact produces a safe
HTTP 503. If an individual restaurant lacks a confidence row inside an otherwise
valid artifact, ranking marks only that factor unavailable and renormalizes its
other active weights rather than inventing a confidence value.

## Bias and limitations

- All current reviews, sources, patterns, and labels are synthetic.
- More observations and sources increase confidence even though quantity does
  not guarantee independence, representativeness, or honesty.
- Rating agreement can reflect shared bias, coordinated behavior, or similar
  audiences; disagreement can reflect legitimate preference differences.
- Vocabulary-based specificity favors reviews that use recognized theme terms.
- Recency can undervalue stable long-running evidence.
- Duplicate and burst flags are controlled ground truth, not production
  detectors. Real deployment would need evaluated detection methods.
- The selected weights, targets, thresholds, and linear formulas are product
  assumptions. They require sensitivity analysis and stakeholder validation
  before real decision use.

The score helps explain evidence quality. It cannot determine whether a review
is true or whether a person will enjoy a restaurant.
