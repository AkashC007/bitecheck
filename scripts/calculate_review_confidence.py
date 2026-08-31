from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Final, Literal, cast


ROOT: Final = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW_PATH: Final = ROOT / "data" / "synthetic" / "reviews.json"
DEFAULT_RESTAURANT_PATH: Final = ROOT / "data" / "synthetic" / "restaurants.json"
DEFAULT_THEME_PATH: Final = ROOT / "data" / "analytics" / "review_themes.json"
DEFAULT_CONFIG_PATH: Final = ROOT / "config" / "review_confidence.json"
DEFAULT_OUTPUT_PATH: Final = ROOT / "data" / "analytics" / "review_confidence.json"
SCORER_VERSION: Final = "1.0.0"
REFERENCE_DATE: Final = date(2026, 1, 15)

ComponentName = Literal[
    "cross_source_agreement",
    "observation_volume",
    "review_recency",
    "source_diversity",
    "review_specificity",
    "branch_match_confidence",
    "rating_consistency",
]
PenaltyName = Literal[
    "exact_duplicates",
    "repetitive_language",
    "suspicious_bursts",
    "missing_data",
]


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def _load(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def _component(
    score: float,
    weight: float,
    explanation: str,
) -> dict[str, object]:
    score = round(_clamp(score), 2)
    return {
        "score": score,
        "weight": weight,
        "contribution": round(score * weight, 2),
        "explanation": explanation,
    }


def calculate_confidence_dataset(
    review_path: Path = DEFAULT_REVIEW_PATH,
    restaurant_path: Path = DEFAULT_RESTAURANT_PATH,
    theme_path: Path = DEFAULT_THEME_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, object]:
    reviews = cast(list[dict[str, object]], _load(review_path)["reviews"])
    restaurants = cast(
        list[dict[str, object]], _load(restaurant_path)["restaurants"]
    )
    analyses = cast(list[dict[str, object]], _load(theme_path)["reviews"])
    config = _load(config_path)
    weights = cast(dict[ComponentName, float], config["component_weights"])
    targets = cast(dict[str, int], config["targets"])
    maximum_penalties = cast(dict[PenaltyName, float], config["maximum_penalties"])
    bands = cast(dict[str, float], config["bands"])

    restaurant_lookup = {
        cast(str, restaurant["restaurant_id"]): restaurant
        for restaurant in restaurants
    }
    theme_count_by_review = {
        cast(str, analysis["review_id"]): cast(int, analysis["theme_count"])
        for analysis in analyses
    }
    reviews_by_restaurant: dict[str, list[dict[str, object]]] = defaultdict(list)
    for review in reviews:
        reviews_by_restaurant[cast(str, review["restaurant_id"])].append(review)

    results: list[dict[str, object]] = []
    for restaurant_id in sorted(reviews_by_restaurant):
        group = reviews_by_restaurant[restaurant_id]
        restaurant = restaurant_lookup[restaurant_id]
        count = len(group)
        ratings = [float(cast(int, review["rating"])) for review in group]
        source_ratings: dict[str, list[float]] = defaultdict(list)
        for review in group:
            source_ratings[cast(str, review["source"])].append(
                float(cast(int, review["rating"]))
            )
        source_means = [statistics.mean(values) for values in source_ratings.values()]
        source_dispersion = statistics.pstdev(source_means) if len(source_means) > 1 else 2.0
        rating_dispersion = statistics.pstdev(ratings) if len(ratings) > 1 else 2.0

        ages = [
            (REFERENCE_DATE - date.fromisoformat(cast(str, review["review_date"]))).days
            for review in group
        ]
        freshness_scores = [
            _clamp(100 * (1 - age / targets["freshness_days"])) for age in ages
        ]
        specificity_scores = [
            _clamp(
                100
                * theme_count_by_review[cast(str, review["review_id"])]
                / targets["specificity_theme_count"]
            )
            for review in group
        ]
        branch_matches = sum(
            review.get("branch_name") == restaurant["name"]
            and review.get("branch_address") == restaurant["address"]
            for review in group
        )

        component_scores: dict[ComponentName, tuple[float, str]] = {
            "cross_source_agreement": (
                _clamp(100 * (1 - source_dispersion / 2)),
                f"Source mean-rating dispersion is {source_dispersion:.2f}.",
            ),
            "observation_volume": (
                _clamp(100 * count / targets["observation_count"]),
                f"{count} observations against a target of {targets['observation_count']}.",
            ),
            "review_recency": (
                statistics.mean(freshness_scores),
                f"Average review age is {statistics.mean(ages):.0f} days.",
            ),
            "source_diversity": (
                _clamp(100 * len(source_ratings) / targets["source_count"]),
                f"{len(source_ratings)} of {targets['source_count']} expected sources present.",
            ),
            "review_specificity": (
                statistics.mean(specificity_scores),
                "Specificity uses extracted theme counts per review.",
            ),
            "branch_match_confidence": (
                100 * branch_matches / count,
                f"{branch_matches} of {count} reviews match branch name and address.",
            ),
            "rating_consistency": (
                _clamp(100 * (1 - rating_dispersion / 2)),
                f"Rating standard deviation is {rating_dispersion:.2f}.",
            ),
        }
        components = {
            name: _component(score, weights[name], explanation)
            for name, (score, explanation) in component_scores.items()
        }
        base_score = round(
            sum(cast(float, value["contribution"]) for value in components.values()),
            2,
        )

        missing_fields = ("review_text", "rating", "review_date", "source", "restaurant_id")
        penalty_rates: dict[PenaltyName, float] = {
            "exact_duplicates": sum(bool(r["is_exact_duplicate"]) for r in group) / count,
            "repetitive_language": sum(bool(r["is_near_duplicate"]) for r in group) / count,
            "suspicious_bursts": sum(bool(r["is_suspicious_burst"]) for r in group) / count,
            "missing_data": sum(
                r.get(field) in (None, "") for r in group for field in missing_fields
            )
            / (count * len(missing_fields)),
        }
        penalties = {
            name: {
                "rate": round(rate, 4),
                "maximum_penalty": maximum_penalties[name],
                "penalty": round(rate * maximum_penalties[name], 2),
                "explanation": f"{round(rate * 100, 1)}% of applicable observations.",
            }
            for name, rate in penalty_rates.items()
        }
        total_penalty = round(
            sum(cast(float, value["penalty"]) for value in penalties.values()), 2
        )
        score = round(_clamp(base_score - total_penalty), 2)
        band = (
            "high"
            if score >= bands["high_minimum"]
            else "medium"
            if score >= bands["medium_minimum"]
            else "low"
        )
        results.append(
            {
                "restaurant_id": restaurant_id,
                "restaurant_name": restaurant["name"],
                "observation_count": count,
                "source_metrics": [
                    {
                        "source": source,
                        "review_count": len(values),
                        "mean_rating": round(statistics.mean(values), 2),
                    }
                    for source, values in sorted(source_ratings.items())
                ],
                "components": components,
                "base_score": base_score,
                "penalties": penalties,
                "total_penalty": total_penalty,
                "review_confidence_score": score,
                "confidence_band": band,
                "interpretation": (
                    "Evidence reliability estimate; not a truth or authenticity score."
                ),
            }
        )

    return {
        "metadata": {
            "dataset_name": "BiteCheck Review Confidence Analytics",
            "scorer_version": SCORER_VERSION,
            "reference_date": REFERENCE_DATE.isoformat(),
            "restaurant_count": len(results),
            "review_count": len(reviews),
            "not_a_truth_score": True,
        },
        "configuration": config,
        "restaurants": results,
    }


def write_confidence_dataset(output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(calculate_confidence_dataset(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate Review Confidence Scores.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    arguments = parser.parse_args()
    print(f"Wrote review confidence analytics to {write_confidence_dataset(arguments.output)}")


if __name__ == "__main__":
    main()
