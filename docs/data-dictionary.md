# Data dictionary

## Dataset

- **Path:** `data/synthetic/restaurants.json`
- **Schema version:** 2.0.0
- **Generator version:** 2.0.0
- **Default seed:** 42
- **Default records:** 24
- **Provenance:** Hybrid. Identity/location/inspection fields are City of
  Chicago public data; recommendation/profile fields are synthetic.

The JSON document contains `metadata` and `restaurants` at its top level.

## Metadata fields

| Field | Type | Description |
| --- | --- | --- |
| `dataset_name` | string | Human-readable dataset name. |
| `description` | string | Purpose and hybrid-data notice. |
| `city` | string | Current dataset city; always `Chicago`. |
| `hybrid` | boolean | Always `true`. |
| `synthetic` | boolean | Always `false`; the entire record is not synthetic. |
| `seed` | integer | Random seed used by the generator. |
| `record_count` | integer | Number of restaurant objects. |
| `generator_version` | string | Version of the generation rules. |
| `schema_version` | string | Version of the output field contract. |
| `identity_source` | string | `City of Chicago Food Inspections`. |
| `identity_source_url` | string | Official dataset page. |
| `identity_snapshot_date` | date | Fixed public-data snapshot date. |
| `synthetic_fields` | array | Exact profile fields added by BiteCheck. |
| `source_disclaimer` | string | Point-in-time inspection limitation. |

## Restaurant fields

| Field | Type | Description and allowed values |
| --- | --- | --- |
| `restaurant_id` | string | `CHI-COC-` plus the City license number. |
| `license_number` | string | City facility license used for deduplication. |
| `name` | string | Public establishment/AKA name from the City dataset. |
| `address` | string | Public establishment address from the City dataset. |
| `city` | string | `Chicago`. Kept as a field so future cities do not require a schema rewrite. |
| `state` | string | `IL`. |
| `zip_code` | string | Public postal code from the City dataset. |
| `neighborhood` | string | Illinois Tech, Chinatown, Chicago Loop, Hyde Park, Bridgeport, Lakeview, or River North. |
| `latitude` | number | Public coordinate from the City dataset. |
| `longitude` | number | Public coordinate from the City dataset. |
| `cuisine` | string | American, Chinese, Ethiopian, Indian, Italian, Japanese, Korean, Mediterranean, Mexican, or Thai. |
| `price_category` | string | `$`, `$$`, or `$$$`. |
| `estimated_cost_per_person` | integer | Synthetic dollar estimate used by the future budget filter. |
| `vegetarian_available` | boolean | Whether synthetic vegetarian availability is present. |
| `vegan_available` | boolean | Whether synthetic vegan availability is present; `true` requires vegetarian availability. |
| `rating` | number | Synthetic rating from 1.0 through 5.0. Current generated range is 3.2–4.8. |
| `review_count` | integer | Nonnegative synthetic review count. |
| `opening_hours` | object | Seven day keys. Each value is an opening period or `null` for closed. |
| `estimated_transportation` | object | Synthetic estimates from every supported starting area. |
| `latest_inspection` | object | Newest inspection in the fixed source window. |
| `inspection_history` | object | Counts by result within the source window. |
| `identity_provenance` | string | Always `city_of_chicago_food_inspections`. |
| `profile_provenance` | string | Always `synthetic_enrichment`. |
| `data_provenance` | string | Always `hybrid`. |

## Latest-inspection fields

| Field | Type | Description |
| --- | --- | --- |
| `inspection_id` | string | City inspection identifier. |
| `inspection_date` | date | Date of the newest inspection in the snapshot window. |
| `result` | string | `Pass` or `Pass w/ Conditions` for included records. |
| `inspection_type` | string | City inspection category. |
| `risk` | string | City-provided facility risk classification. |

These results are point-in-time observations and do not guarantee current
operation, current conditions, or safety.

## Price mapping

| Category | Generated cost per person |
| --- | ---: |
| `$` | $10–$18 |
| `$$` | $19–$35 |
| `$$$` | $36–$60 |

## Opening-period fields

| Field | Type | Description |
| --- | --- | --- |
| `open` | string | 24-hour time formatted `HH:MM`. |
| `close` | string | 24-hour time formatted `HH:MM` and later than `open`. |

Every restaurant is open at least six days in the current synthetic rules.

## Transportation-estimate fields

Each restaurant contains an estimate from all seven supported starting areas.

| Field | Type | Description |
| --- | --- | --- |
| `straight_line_distance_km` | number | Haversine distance between synthetic coordinates. |
| `walking_minutes` | integer | Positive synthetic walking estimate. |
| `public_transit_minutes` | integer | Positive synthetic transit estimate. |
| `driving_minutes` | integer | Positive synthetic driving estimate. |
| `estimate_type` | string | Always `synthetic`. |

These estimates are useful for software testing and are not real routing
directions or travel advice.

## Enforced quality rules

- Required fields must be present with no unexpected fields.
- IDs, selected names, and selected addresses must be unique.
- Coordinates must remain within broad Chicago bounds.
- Every configured cuisine and starting area must be represented.
- Costs must agree with their price category.
- Vegan availability cannot exist without vegetarian availability.
- Opening hours must include all seven days and valid times.
- Transportation times must be positive and labeled synthetic.
- The latest included City result must be `Pass` or `Pass w/ Conditions`.
- The committed file must exactly match the default generator output.

## Synthetic review dataset

- **Path:** `data/synthetic/reviews.json`
- **Schema/generator version:** 1.0.0
- **Seed:** 84
- **Fixed reference date:** 2026-01-15
- **Records:** 288 (12 for each restaurant branch)
- **Sources:** three explicitly fictional source names

| Field | Type | Description |
| --- | --- | --- |
| `review_id` | string | Unique BiteCheck synthetic review identifier. |
| `restaurant_id` | string | Foreign key to the restaurant branch. |
| `branch_name`, `branch_address` | string | Denormalized linkage checks. |
| `source`, `source_review_id` | string | Fictional source and unique source record ID. |
| `synthetic_reviewer_id` | string | Fictional reviewer identity for test patterns. |
| `review_text` | string | Generated unstructured review text. |
| `rating` | integer | Synthetic 1–5 scale; generated records use 2–5. |
| `review_date` | date string | ISO `YYYY-MM-DD`, never after the reference date. |
| `sentiment_label` | string | Expected `positive`, `negative`, or `mixed`. |
| `expected_aspects` | array | Ground-truth theme/sentiment pairs for evaluation. |
| `is_exact_duplicate` | boolean | Whether text exactly copies a linked review. |
| `duplicate_of_review_id` | string/null | Exact-duplicate parent. |
| `is_near_duplicate` | boolean | Whether text closely modifies a linked review. |
| `near_duplicate_of_review_id` | string/null | Near-duplicate parent. |
| `is_old_review` | boolean | More than 730 days before the reference date. |
| `is_suspicious_burst` | boolean | Member of a controlled short-window burst. |
| `burst_group_id` | string/null | Synthetic burst lineage group. |
| `data_provenance` | string | Always `synthetic`. |

The labels are test ground truth, not production detection results. Text is
template-generated and cannot represent the full vocabulary, culture, or bias
of real restaurant reviews.

## Review Confidence analytics

- **Path:** `data/analytics/review_confidence.json`
- **Scorer version:** 1.0.0
- **Rows:** 24 restaurant branches

Each row stores `restaurant_id`, `restaurant_name`, observation count,
per-source review count and mean rating, seven named component objects, the
weighted `base_score`, four named penalty objects, `total_penalty`, the final
`review_confidence_score`, its low/medium/high band, and a non-truth-score
interpretation. Component objects contain score, weight, contribution, and
explanation. Penalty objects contain affected rate, cap, deduction, and
explanation.

## Recommendation insights

- **Path:** `data/analytics/recommendation_insights.json`
- **Builder version:** 1.0.0
- **Rows:** 24 restaurant branches

| Field | Type | Description |
| --- | --- | --- |
| `restaurant_id` | string | Join key to restaurant, confidence, and ranking rows. |
| `observation_count` | integer | Full source review count for the branch. |
| `latest_review_date` | date string | Latest synthetic review date. |
| `positive_theme_mentions` | integer | Positive mentions after exact-duplicate exclusion. |
| `negative_theme_mentions` | integer | Negative mentions after exact-duplicate exclusion. |
| `positive_theme_counts` | object | All positive mention counts keyed by theme for follow-up sorting. |
| `negative_theme_counts` | object | All negative mention counts keyed by theme. |
| `top_positive_themes` | array | Up to three theme, label, and mention-count objects. |
| `top_negative_themes` | array | Up to three theme, label, and mention-count objects. |

The artifact metadata records that 24 exact-duplicate reviews were excluded
from display frequencies. Near-duplicates remain part of the current counts.
