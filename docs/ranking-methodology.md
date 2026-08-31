# Ranking methodology

`POST /restaurants/rank` first applies structured filters, then scores only
matching restaurants. Default weights live in `config/ranking_weights.json`.

## Normalized scores

- Cuisine and dietary matches score 100 when requested and satisfied.
- Budget: `100 × (1 - cost / (2 × budget))`, clamped to 0–100.
- Travel: `100 × (1 - minutes / (2 × limit))`, clamped to 0–100.
- Rating: `(rating - 1) / 4 × 100`.
- Review Confidence uses the validated per-branch 0–100 evidence-reliability
  score calculated in Milestone 9. It is not a truth score.

Only active factors receive effective weight. Missing weights are redistributed
proportionally. Contribution equals normalized score times effective weight;
the 0–100 total is the contribution sum. Equal totals share a rank and retain
stable dataset order. Every factor reports its status and explanation.

This is a transparent decision model, not objective truth. Current ratings and
travel values are synthetic; opening status and broader preferences are future
inputs.
