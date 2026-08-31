from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Final, Literal, TypedDict, cast


ROOT: Final = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH: Final = ROOT / "data" / "synthetic" / "reviews.json"
DEFAULT_OUTPUT_PATH: Final = ROOT / "data" / "analytics" / "review_themes.json"
ANALYZER_VERSION: Final = "1.0.0"
Sentiment = Literal["positive", "negative", "neutral", "mixed"]

THEME_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "food_quality": ("fresh", "flavorful", "excellent", "bland", "food quality"),
    "specific_dishes": (
        "griddle plate", "noodles", "injera platter", "masala", "pasta",
        "miso bowl", "banchan", "mezze plate", "tacos", "basil noodles",
    ),
    "authenticity": ("authentic", "authenticity"),
    "service": ("service", "server", "staff"),
    "price": ("price", "prices", "expensive"),
    "value": ("value", "worth"),
    "portion_size": ("portion", "portions"),
    "waiting_time": ("wait", "waited", "slow", "longer than expected"),
    "atmosphere": ("atmosphere", "dining room", "welcoming"),
    "cleanliness": ("clean", "dirty", "cleanliness"),
    "vegetarian_options": ("vegetarian",),
    "vegan_options": ("vegan",),
    "parking": ("parking",),
    "public_transit_convenience": ("public transit", "transit stop"),
    "spice_level": ("spice", "spicy"),
}

POSITIVE_TERMS: Final = (
    "fresh", "flavorful", "friendly", "generous", "good", "welcoming",
    "clean", "excellent", "convenient", "varied", "clearly described",
    "easy to identify", "authentic", "gladly return",
)
NEGATIVE_TERMS: Final = (
    "bland", "slow", "uneven", "high", "small", "poor", "difficult",
    "limited", "could not", "longer than expected", "dirty", "expensive",
)


class AspectPrediction(TypedDict):
    theme: str
    sentiment: Literal["positive", "negative", "neutral"]
    evidence: str


class ReviewAnalysis(TypedDict):
    review_id: str
    restaurant_id: str
    source: str
    normalized_text: str
    overall_sentiment: Sentiment
    theme_count: int
    aspects: list[AspectPrediction]


def normalize_review_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = re.sub(r"[^\w\s$'-]", " ", normalized)
    return " ".join(normalized.split())


def _clauses(text: str) -> list[str]:
    return [
        clause.strip()
        for clause in re.split(r"\bbut\b|\balthough\b|\bso\b|,|;", text)
        if clause.strip()
    ]


def _contains_term(clause: str, term: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", clause) is not None


def _clause_sentiment(clause: str) -> Literal["positive", "negative", "neutral"]:
    positive = sum(_contains_term(clause, term) for term in POSITIVE_TERMS)
    negative = sum(_contains_term(clause, term) for term in NEGATIVE_TERMS)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "neutral"


def analyze_review(
    review_id: str,
    restaurant_id: str,
    source: str,
    review_text: str,
) -> ReviewAnalysis:
    normalized = normalize_review_text(review_text)
    predictions: dict[str, AspectPrediction] = {}
    for clause in _clauses(normalized):
        sentiment = _clause_sentiment(clause)
        for theme, terms in THEME_TERMS.items():
            if any(_contains_term(clause, term) for term in terms):
                existing = predictions.get(theme)
                if existing is None or existing["sentiment"] == "neutral":
                    predictions[theme] = {
                        "theme": theme,
                        "sentiment": sentiment,
                        "evidence": clause,
                    }

    sentiments = {prediction["sentiment"] for prediction in predictions.values()}
    non_neutral = sentiments - {"neutral"}
    overall: Sentiment
    if non_neutral == {"positive", "negative"}:
        overall = "mixed"
    elif non_neutral == {"positive"}:
        overall = "positive"
    elif non_neutral == {"negative"}:
        overall = "negative"
    else:
        overall = "neutral"
    aspects = sorted(predictions.values(), key=lambda item: item["theme"])
    return {
        "review_id": review_id,
        "restaurant_id": restaurant_id,
        "source": source,
        "normalized_text": normalized,
        "overall_sentiment": overall,
        "theme_count": len(aspects),
        "aspects": aspects,
    }


def analyze_dataset(input_path: Path = DEFAULT_INPUT_PATH) -> dict[str, object]:
    payload = cast(dict[str, object], json.loads(input_path.read_text(encoding="utf-8")))
    reviews = cast(list[dict[str, object]], payload["reviews"])
    analyses = [
        analyze_review(
            review_id=cast(str, review["review_id"]),
            restaurant_id=cast(str, review["restaurant_id"]),
            source=cast(str, review["source"]),
            review_text=cast(str, review["review_text"]),
        )
        for review in reviews
    ]

    predicted_pairs = {
        (analysis["review_id"], aspect["theme"], aspect["sentiment"])
        for analysis in analyses
        for aspect in analysis["aspects"]
    }
    expected_pairs = {
        (
            cast(str, review["review_id"]),
            cast(str, aspect["theme"]),
            cast(str, aspect["sentiment"]),
        )
        for review in reviews
        for aspect in cast(list[dict[str, object]], review["expected_aspects"])
    }
    true_positive = len(predicted_pairs & expected_pairs)
    precision = true_positive / len(predicted_pairs) if predicted_pairs else 0.0
    recall = true_positive / len(expected_pairs) if expected_pairs else 0.0
    theme_counts: Counter[str] = Counter()
    sentiment_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for analysis in analyses:
        for aspect in analysis["aspects"]:
            theme_counts[aspect["theme"]] += 1
            sentiment_counts[aspect["theme"]][aspect["sentiment"]] += 1

    return {
        "metadata": {
            "dataset_name": "BiteCheck Review Theme Analytics",
            "analyzer_version": ANALYZER_VERSION,
            "input_record_count": len(reviews),
            "analyzed_record_count": len(analyses),
            "synthetic_input": True,
        },
        "evaluation": {
            "expected_aspect_sentiment_pairs": len(expected_pairs),
            "predicted_aspect_sentiment_pairs": len(predicted_pairs),
            "true_positive_pairs": true_positive,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(
                2 * precision * recall / (precision + recall)
                if precision + recall
                else 0.0,
                4,
            ),
        },
        "theme_summary": {
            theme: {
                "mention_count": theme_counts[theme],
                "sentiment_counts": dict(sorted(sentiment_counts[theme].items())),
            }
            for theme in sorted(THEME_TERMS)
        },
        "reviews": analyses,
    }


def write_analysis(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    input_path: Path = DEFAULT_INPUT_PATH,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(analyze_dataset(input_path), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze synthetic review themes.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    arguments = parser.parse_args()
    print(f"Wrote review theme analysis to {write_analysis(arguments.output, arguments.input)}")


if __name__ == "__main__":
    main()
