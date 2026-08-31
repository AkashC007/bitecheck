from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Final, cast


ROOT: Final = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW_PATH: Final = ROOT / "data" / "synthetic" / "reviews.json"
DEFAULT_THEME_PATH: Final = ROOT / "data" / "analytics" / "review_themes.json"
DEFAULT_OUTPUT_PATH: Final = ROOT / "data" / "analytics" / "recommendation_insights.json"
BUILDER_VERSION: Final = "1.0.0"
THEME_LIMIT: Final = 3


def _load(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def _theme_label(theme: str) -> str:
    return theme.replace("_", " ").capitalize()


def _top_themes(counter: Counter[str]) -> list[dict[str, object]]:
    return [
        {
            "theme": theme,
            "label": _theme_label(theme),
            "mention_count": count,
        }
        for theme, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[
            :THEME_LIMIT
        ]
    ]


def build_recommendation_insights(
    review_path: Path = DEFAULT_REVIEW_PATH,
    theme_path: Path = DEFAULT_THEME_PATH,
) -> dict[str, object]:
    review_payload = _load(review_path)
    reviews = cast(list[dict[str, object]], review_payload["reviews"])
    analyses = cast(list[dict[str, object]], _load(theme_path)["reviews"])
    review_by_id = {
        cast(str, review["review_id"]): review for review in reviews
    }

    positive: dict[str, Counter[str]] = defaultdict(Counter)
    negative: dict[str, Counter[str]] = defaultdict(Counter)
    excluded_exact_duplicates = 0
    for analysis in analyses:
        review_id = cast(str, analysis["review_id"])
        source_review = review_by_id[review_id]
        if cast(bool, source_review["is_exact_duplicate"]):
            excluded_exact_duplicates += 1
            continue
        restaurant_id = cast(str, analysis["restaurant_id"])
        aspects = cast(list[dict[str, object]], analysis["aspects"])
        for aspect in aspects:
            sentiment = cast(str, aspect["sentiment"])
            theme = cast(str, aspect["theme"])
            if sentiment == "positive":
                positive[restaurant_id][theme] += 1
            elif sentiment == "negative":
                negative[restaurant_id][theme] += 1

    reviews_by_restaurant: dict[str, list[dict[str, object]]] = defaultdict(list)
    for review in reviews:
        reviews_by_restaurant[cast(str, review["restaurant_id"])].append(review)

    results: list[dict[str, object]] = []
    for restaurant_id in sorted(reviews_by_restaurant):
        group = reviews_by_restaurant[restaurant_id]
        positive_counter = positive[restaurant_id]
        negative_counter = negative[restaurant_id]
        results.append(
            {
                "restaurant_id": restaurant_id,
                "observation_count": len(group),
                "latest_review_date": max(
                    cast(str, review["review_date"]) for review in group
                ),
                "positive_theme_mentions": sum(positive_counter.values()),
                "negative_theme_mentions": sum(negative_counter.values()),
                "positive_theme_counts": dict(sorted(positive_counter.items())),
                "negative_theme_counts": dict(sorted(negative_counter.items())),
                "top_positive_themes": _top_themes(positive_counter),
                "top_negative_themes": _top_themes(negative_counter),
            }
        )

    return {
        "metadata": {
            "dataset_name": "BiteCheck Recommendation Insights",
            "builder_version": BUILDER_VERSION,
            "restaurant_count": len(results),
            "review_count": len(reviews),
            "excluded_exact_duplicate_reviews": excluded_exact_duplicates,
            "theme_limit_per_sentiment": THEME_LIMIT,
            "synthetic_input": True,
        },
        "restaurants": results,
    }


def write_recommendation_insights(output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(build_recommendation_insights(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build card-ready restaurant review insights."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    arguments = parser.parse_args()
    print(f"Wrote recommendation insights to {write_recommendation_insights(arguments.output)}")


if __name__ == "__main__":
    main()
