from __future__ import annotations

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Final, Literal, TypedDict, cast


DEFAULT_SEED: Final = 84
REVIEWS_PER_RESTAURANT: Final = 12
REFERENCE_DATE: Final = date(2026, 1, 15)
GENERATOR_VERSION: Final = "1.0.0"
SCHEMA_VERSION: Final = "1.0.0"
ROOT: Final = Path(__file__).resolve().parents[1]
DEFAULT_RESTAURANT_PATH: Final = ROOT / "data" / "synthetic" / "restaurants.json"
DEFAULT_OUTPUT_PATH: Final = ROOT / "data" / "synthetic" / "reviews.json"

SOURCES: Final = (
    "BiteCheck Community Synthetic",
    "CityEats Demo",
    "DineLog Synthetic",
)

DISHES: Final[dict[str, str]] = {
    "American": "griddle plate",
    "Chinese": "noodles",
    "Ethiopian": "injera platter",
    "Indian": "masala",
    "Italian": "pasta",
    "Japanese": "miso bowl",
    "Korean": "banchan",
    "Mediterranean": "mezze plate",
    "Mexican": "tacos",
    "Thai": "basil noodles",
}

Sentiment = Literal["positive", "negative", "mixed"]
AspectSentiment = Literal["positive", "negative", "neutral"]


class AspectLabel(TypedDict):
    theme: str
    sentiment: AspectSentiment


class RestaurantInput(TypedDict):
    restaurant_id: str
    name: str
    address: str
    cuisine: str
    vegetarian_available: bool
    vegan_available: bool


class Review(TypedDict):
    review_id: str
    restaurant_id: str
    branch_name: str
    branch_address: str
    source: str
    source_review_id: str
    synthetic_reviewer_id: str
    review_text: str
    rating: int
    review_date: str
    sentiment_label: Sentiment
    expected_aspects: list[AspectLabel]
    is_exact_duplicate: bool
    duplicate_of_review_id: str | None
    is_near_duplicate: bool
    near_duplicate_of_review_id: str | None
    is_old_review: bool
    is_suspicious_burst: bool
    burst_group_id: str | None
    data_provenance: Literal["synthetic"]


class ReviewDataset(TypedDict):
    metadata: dict[str, object]
    reviews: list[Review]


class Blueprint(TypedDict):
    text: str
    rating: int
    sentiment: Sentiment
    aspects: list[AspectLabel]


def _aspect(theme: str, sentiment: AspectSentiment) -> AspectLabel:
    return {"theme": theme, "sentiment": sentiment}


def _blueprints(restaurant: RestaurantInput) -> list[Blueprint]:
    dish = DISHES[restaurant["cuisine"]]
    vegetarian_text = (
        "The vegetarian options were varied and clearly described."
        if restaurant["vegetarian_available"]
        else "Vegetarian choices were very limited."
    )
    vegetarian_sentiment: AspectSentiment = (
        "positive" if restaurant["vegetarian_available"] else "negative"
    )
    vegan_text = (
        "The vegan options were easy to identify."
        if restaurant["vegan_available"]
        else "I could not find a clearly marked vegan option."
    )
    vegan_sentiment: AspectSentiment = (
        "positive" if restaurant["vegan_available"] else "negative"
    )
    return [
        {
            "text": f"The {dish} tasted fresh and flavorful, and service was friendly.",
            "rating": 5,
            "sentiment": "positive",
            "aspects": [
                _aspect("specific_dishes", "positive"),
                _aspect("food_quality", "positive"),
                _aspect("service", "positive"),
            ],
        },
        {
            "text": "The portions were generous and the meal felt like good value.",
            "rating": 4,
            "sentiment": "positive",
            "aspects": [
                _aspect("portion_size", "positive"),
                _aspect("value", "positive"),
            ],
        },
        {
            "text": "The dining room felt welcoming and looked very clean.",
            "rating": 5,
            "sentiment": "positive",
            "aspects": [
                _aspect("atmosphere", "positive"),
                _aspect("cleanliness", "positive"),
            ],
        },
        {
            "text": f"The {dish} was excellent, but the service was slow.",
            "rating": 3,
            "sentiment": "mixed",
            "aspects": [
                _aspect("specific_dishes", "positive"),
                _aspect("food_quality", "positive"),
                _aspect("service", "negative"),
                _aspect("waiting_time", "negative"),
            ],
        },
        {
            "text": f"The {dish} was bland and the spice level felt uneven.",
            "rating": 2,
            "sentiment": "negative",
            "aspects": [
                _aspect("specific_dishes", "negative"),
                _aspect("food_quality", "negative"),
                _aspect("spice_level", "negative"),
            ],
        },
        {
            "text": "Prices felt high for the small portions, so the value was poor.",
            "rating": 2,
            "sentiment": "negative",
            "aspects": [
                _aspect("price", "negative"),
                _aspect("portion_size", "negative"),
                _aspect("value", "negative"),
            ],
        },
        {
            "text": "Parking was difficult, but the public-transit stop was convenient.",
            "rating": 3,
            "sentiment": "mixed",
            "aspects": [
                _aspect("parking", "negative"),
                _aspect("public_transit_convenience", "positive"),
            ],
        },
        {
            "text": vegetarian_text,
            "rating": 4 if restaurant["vegetarian_available"] else 2,
            "sentiment": (
                "positive" if restaurant["vegetarian_available"] else "negative"
            ),
            "aspects": [_aspect("vegetarian_options", vegetarian_sentiment)],
        },
        {
            "text": vegan_text,
            "rating": 4 if restaurant["vegan_available"] else 2,
            "sentiment": (
                "positive" if restaurant["vegan_available"] else "negative"
            ),
            "aspects": [_aspect("vegan_options", vegan_sentiment)],
        },
        {
            "text": f"The {dish} seemed authentic, although the wait was longer than expected.",
            "rating": 3,
            "sentiment": "mixed",
            "aspects": [
                _aspect("authenticity", "positive"),
                _aspect("waiting_time", "negative"),
            ],
        },
    ]


def _load_restaurants(path: Path) -> list[RestaurantInput]:
    payload = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
    return cast(list[RestaurantInput], payload["restaurants"])


def generate_review_dataset(
    seed: int = DEFAULT_SEED,
    restaurant_path: Path = DEFAULT_RESTAURANT_PATH,
) -> ReviewDataset:
    rng = random.Random(seed)
    restaurants = _load_restaurants(restaurant_path)
    reviews: list[Review] = []
    next_id = 1

    for restaurant_index, restaurant in enumerate(restaurants, start=1):
        blueprints = _blueprints(restaurant)
        restaurant_reviews: list[Review] = []
        burst_group = (
            f"BURST-SYN-{restaurant_index:03d}" if restaurant_index <= 6 else None
        )
        burst_date = REFERENCE_DATE - timedelta(days=restaurant_index * 3)

        for local_index, blueprint in enumerate(blueprints):
            is_old = local_index == 9
            is_burst = burst_group is not None and 2 <= local_index <= 5
            review_date = (
                REFERENCE_DATE - timedelta(days=rng.randint(900, 1_500))
                if is_old
                else burst_date + timedelta(days=local_index % 2)
                if is_burst
                else REFERENCE_DATE - timedelta(days=rng.randint(0, 540))
            )
            review_id = f"REV-SYN-{next_id:06d}"
            next_id += 1
            restaurant_reviews.append(
                {
                    "review_id": review_id,
                    "restaurant_id": restaurant["restaurant_id"],
                    "branch_name": restaurant["name"],
                    "branch_address": restaurant["address"],
                    "source": SOURCES[(local_index + restaurant_index) % len(SOURCES)],
                    "source_review_id": f"SRC-SYN-{next_id - 1:06d}",
                    "synthetic_reviewer_id": (
                        f"USER-SYN-{restaurant_index:03d}-{local_index:02d}"
                    ),
                    "review_text": blueprint["text"],
                    "rating": blueprint["rating"],
                    "review_date": review_date.isoformat(),
                    "sentiment_label": blueprint["sentiment"],
                    "expected_aspects": blueprint["aspects"],
                    "is_exact_duplicate": False,
                    "duplicate_of_review_id": None,
                    "is_near_duplicate": False,
                    "near_duplicate_of_review_id": None,
                    "is_old_review": is_old,
                    "is_suspicious_burst": is_burst,
                    "burst_group_id": burst_group if is_burst else None,
                    "data_provenance": "synthetic",
                }
            )

        exact_source = restaurant_reviews[0]
        near_source = restaurant_reviews[1]
        for kind, source_review in (("exact", exact_source), ("near", near_source)):
            review_id = f"REV-SYN-{next_id:06d}"
            next_id += 1
            is_exact = kind == "exact"
            review_text = (
                source_review["review_text"]
                if is_exact
                else f"{source_review['review_text']} I would gladly return."
            )
            restaurant_reviews.append(
                {
                    **source_review,
                    "review_id": review_id,
                    "source": SOURCES[
                        (SOURCES.index(source_review["source"]) + 1) % len(SOURCES)
                    ],
                    "source_review_id": f"SRC-SYN-{next_id - 1:06d}",
                    "review_text": review_text,
                    "review_date": (
                        date.fromisoformat(source_review["review_date"])
                        + timedelta(days=1)
                    ).isoformat(),
                    "is_exact_duplicate": is_exact,
                    "duplicate_of_review_id": (
                        source_review["review_id"] if is_exact else None
                    ),
                    "is_near_duplicate": not is_exact,
                    "near_duplicate_of_review_id": (
                        source_review["review_id"] if not is_exact else None
                    ),
                    "is_old_review": False,
                    "is_suspicious_burst": False,
                    "burst_group_id": None,
                }
            )

        reviews.extend(restaurant_reviews)

    metadata: dict[str, object] = {
        "dataset_name": "BiteCheck Synthetic Multi-Source Reviews",
        "description": "Fictional reviews with labeled analysis edge cases.",
        "synthetic": True,
        "seed": seed,
        "reference_date": REFERENCE_DATE.isoformat(),
        "record_count": len(reviews),
        "restaurant_count": len(restaurants),
        "reviews_per_restaurant": REVIEWS_PER_RESTAURANT,
        "sources": list(SOURCES),
        "exact_duplicate_count": sum(r["is_exact_duplicate"] for r in reviews),
        "near_duplicate_count": sum(r["is_near_duplicate"] for r in reviews),
        "old_review_count": sum(r["is_old_review"] for r in reviews),
        "suspicious_burst_review_count": sum(
            r["is_suspicious_burst"] for r in reviews
        ),
        "generator_version": GENERATOR_VERSION,
        "schema_version": SCHEMA_VERSION,
    }
    return {"metadata": metadata, "reviews": reviews}


def write_review_dataset(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    seed: int = DEFAULT_SEED,
    restaurant_path: Path = DEFAULT_RESTAURANT_PATH,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            generate_review_dataset(seed=seed, restaurant_path=restaurant_path),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return output_path.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic review data.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--restaurant-path", type=Path, default=DEFAULT_RESTAURANT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    arguments = parser.parse_args()
    written = write_review_dataset(
        output_path=arguments.output,
        seed=arguments.seed,
        restaurant_path=arguments.restaurant_path,
    )
    print(f"Wrote synthetic review dataset to {written}")


if __name__ == "__main__":
    main()
