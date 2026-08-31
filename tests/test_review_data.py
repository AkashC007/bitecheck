import json
from collections import Counter, defaultdict
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from typing import cast

from scripts.generate_review_data import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SEED,
    REFERENCE_DATE,
    REVIEWS_PER_RESTAURANT,
    SOURCES,
    ReviewDataset,
    generate_review_dataset,
    write_review_dataset,
)


EXPECTED_REVIEW_FIELDS = {
    "review_id",
    "restaurant_id",
    "branch_name",
    "branch_address",
    "source",
    "source_review_id",
    "synthetic_reviewer_id",
    "review_text",
    "rating",
    "review_date",
    "sentiment_label",
    "expected_aspects",
    "is_exact_duplicate",
    "duplicate_of_review_id",
    "is_near_duplicate",
    "near_duplicate_of_review_id",
    "is_old_review",
    "is_suspicious_burst",
    "burst_group_id",
    "data_provenance",
}

EXPECTED_THEMES = {
    "food_quality",
    "specific_dishes",
    "authenticity",
    "service",
    "price",
    "value",
    "portion_size",
    "waiting_time",
    "atmosphere",
    "cleanliness",
    "vegetarian_options",
    "vegan_options",
    "parking",
    "public_transit_convenience",
    "spice_level",
}


def load_committed_reviews() -> ReviewDataset:
    return cast(
        ReviewDataset,
        json.loads(DEFAULT_OUTPUT_PATH.read_text(encoding="utf-8")),
    )


def load_restaurant_lookup() -> dict[str, dict[str, object]]:
    path = DEFAULT_OUTPUT_PATH.with_name("restaurants.json")
    payload = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
    restaurants = cast(list[dict[str, object]], payload["restaurants"])
    return {cast(str, item["restaurant_id"]): item for item in restaurants}


def test_review_dataset_is_reproducible_and_seeded() -> None:
    assert generate_review_dataset() == generate_review_dataset()
    assert generate_review_dataset()["metadata"]["seed"] == DEFAULT_SEED
    assert generate_review_dataset(seed=DEFAULT_SEED + 1) != generate_review_dataset()


def test_write_review_dataset_creates_expected_json(tmp_path: Path) -> None:
    output = tmp_path / "reviews.json"

    written = write_review_dataset(output_path=output)

    assert written == output.resolve()
    assert json.loads(output.read_text(encoding="utf-8")) == generate_review_dataset()


def test_committed_review_dataset_matches_generator() -> None:
    assert load_committed_reviews() == generate_review_dataset()


def test_review_metadata_reconciles_to_records() -> None:
    dataset = load_committed_reviews()
    metadata = dataset["metadata"]
    reviews = dataset["reviews"]

    assert metadata["synthetic"] is True
    assert metadata["record_count"] == 288
    assert metadata["restaurant_count"] == 24
    assert metadata["reviews_per_restaurant"] == REVIEWS_PER_RESTAURANT
    assert metadata["sources"] == list(SOURCES)
    assert len(reviews) == 288
    assert set(Counter(review["restaurant_id"] for review in reviews).values()) == {
        REVIEWS_PER_RESTAURANT
    }
    assert Counter(review["source"] for review in reviews) == {
        source: 96 for source in SOURCES
    }


def test_reviews_have_valid_fields_labels_and_restaurant_links() -> None:
    reviews = load_committed_reviews()["reviews"]
    restaurants = load_restaurant_lookup()
    review_ids = {review["review_id"] for review in reviews}
    source_ids = {review["source_review_id"] for review in reviews}

    assert len(review_ids) == len(reviews)
    assert len(source_ids) == len(reviews)
    for review in reviews:
        restaurant = restaurants[review["restaurant_id"]]
        assert set(review) == EXPECTED_REVIEW_FIELDS
        assert review["branch_name"] == restaurant["name"]
        assert review["branch_address"] == restaurant["address"]
        assert review["source"] in SOURCES
        assert review["review_text"].strip()
        assert review["rating"] in {1, 2, 3, 4, 5}
        assert review["sentiment_label"] in {"positive", "negative", "mixed"}
        assert date.fromisoformat(review["review_date"]) <= REFERENCE_DATE
        assert review["data_provenance"] == "synthetic"
        assert review["expected_aspects"]
        for aspect in review["expected_aspects"]:
            assert aspect["theme"] in EXPECTED_THEMES
            assert aspect["sentiment"] in {"positive", "negative", "neutral"}


def test_dataset_covers_all_planned_sentiments_ratings_and_themes() -> None:
    reviews = load_committed_reviews()["reviews"]

    assert {review["sentiment_label"] for review in reviews} == {
        "positive",
        "negative",
        "mixed",
    }
    assert {review["rating"] for review in reviews} == {2, 3, 4, 5}
    assert {
        aspect["theme"]
        for review in reviews
        for aspect in review["expected_aspects"]
    } == EXPECTED_THEMES


def test_exact_and_near_duplicate_lineage_is_valid() -> None:
    reviews = load_committed_reviews()["reviews"]
    by_id = {review["review_id"]: review for review in reviews}
    exact = [review for review in reviews if review["is_exact_duplicate"]]
    near = [review for review in reviews if review["is_near_duplicate"]]

    assert len(exact) == 24
    assert len(near) == 24
    for review in exact:
        source = by_id[cast(str, review["duplicate_of_review_id"])]
        assert review["review_text"] == source["review_text"]
        assert review["restaurant_id"] == source["restaurant_id"]
        assert review["source"] != source["source"]
    for review in near:
        source = by_id[cast(str, review["near_duplicate_of_review_id"])]
        assert review["review_text"] != source["review_text"]
        assert review["restaurant_id"] == source["restaurant_id"]
        assert SequenceMatcher(
            None, review["review_text"], source["review_text"]
        ).ratio() > 0.75


def test_old_reviews_use_fixed_two_year_rule() -> None:
    reviews = load_committed_reviews()["reviews"]
    old = [review for review in reviews if review["is_old_review"]]

    assert len(old) == 24
    assert all(
        (REFERENCE_DATE - date.fromisoformat(review["review_date"])).days > 730
        for review in old
    )


def test_suspicious_burst_groups_have_four_reviews_within_one_day() -> None:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for review in load_committed_reviews()["reviews"]:
        if review["burst_group_id"] is not None:
            groups[review["burst_group_id"]].append(cast(dict[str, object], review))

    assert len(groups) == 6
    assert sum(len(group) for group in groups.values()) == 24
    for group in groups.values():
        dates = [date.fromisoformat(cast(str, review["review_date"])) for review in group]
        assert len(group) == 4
        assert len({review["restaurant_id"] for review in group}) == 1
        assert (max(dates) - min(dates)).days <= 1
        assert all(cast(bool, review["is_suspicious_burst"]) for review in group)
