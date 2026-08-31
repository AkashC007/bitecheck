import json
import re
from pathlib import Path
from typing import cast

import pytest

from scripts.generate_demo_data import (
    CUISINES,
    DAYS,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_RESTAURANT_COUNT,
    DEFAULT_SEED,
    FICTIONAL_STREETS,
    NEIGHBORHOODS,
    PRICE_RANGES,
    Dataset,
    generate_dataset,
    write_dataset,
)


EXPECTED_RESTAURANT_FIELDS = {
    "restaurant_id",
    "name",
    "address",
    "city",
    "state",
    "neighborhood",
    "latitude",
    "longitude",
    "cuisine",
    "price_category",
    "estimated_cost_per_person",
    "vegetarian_available",
    "vegan_available",
    "rating",
    "review_count",
    "opening_hours",
    "estimated_transportation",
    "data_provenance",
}

TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def _load_committed_dataset() -> Dataset:
    return cast(
        Dataset,
        json.loads(DEFAULT_OUTPUT_PATH.read_text(encoding="utf-8")),
    )


def test_default_dataset_is_reproducible() -> None:
    first_run = generate_dataset()
    second_run = generate_dataset()

    assert first_run == second_run
    assert first_run["metadata"]["seed"] == DEFAULT_SEED


def test_different_seed_changes_generated_records() -> None:
    first_run = generate_dataset(seed=DEFAULT_SEED)
    second_run = generate_dataset(seed=DEFAULT_SEED + 1)

    assert first_run["restaurants"] != second_run["restaurants"]


def test_generator_rejects_non_positive_record_count() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        generate_dataset(count=0)


def test_write_dataset_creates_expected_json(tmp_path: Path) -> None:
    output_path = tmp_path / "restaurants.json"

    result_path = write_dataset(output_path=output_path)
    written_dataset = cast(
        Dataset,
        json.loads(output_path.read_text(encoding="utf-8")),
    )

    assert result_path == output_path.resolve()
    assert written_dataset == generate_dataset()


def test_committed_dataset_matches_generator() -> None:
    assert _load_committed_dataset() == generate_dataset()


def test_committed_dataset_has_valid_restaurant_records() -> None:
    dataset = _load_committed_dataset()
    metadata = dataset["metadata"]
    restaurants = dataset["restaurants"]

    assert metadata["synthetic"] is True
    assert metadata["city"] == "Chicago"
    assert metadata["record_count"] == DEFAULT_RESTAURANT_COUNT
    assert len(restaurants) == DEFAULT_RESTAURANT_COUNT

    restaurant_ids = [restaurant["restaurant_id"] for restaurant in restaurants]
    restaurant_names = [restaurant["name"] for restaurant in restaurants]
    restaurant_addresses = [restaurant["address"] for restaurant in restaurants]

    assert len(restaurant_ids) == len(set(restaurant_ids))
    assert len(restaurant_names) == len(set(restaurant_names))
    assert len(restaurant_addresses) == len(set(restaurant_addresses))
    assert {restaurant["cuisine"] for restaurant in restaurants} == set(CUISINES)
    assert {restaurant["neighborhood"] for restaurant in restaurants} == set(
        NEIGHBORHOODS
    )
    assert any(restaurant["vegetarian_available"] for restaurant in restaurants)
    assert any(restaurant["vegan_available"] for restaurant in restaurants)

    for restaurant in restaurants:
        assert set(restaurant) == EXPECTED_RESTAURANT_FIELDS
        assert restaurant["restaurant_id"].startswith("CHI-SYN-")
        assert restaurant["city"] == "Chicago"
        assert restaurant["state"] == "IL"
        assert restaurant["data_provenance"] == "synthetic"
        assert any(
            street_name in restaurant["address"]
            for street_name in FICTIONAL_STREETS
        )
        assert 41.64 <= restaurant["latitude"] <= 42.03
        assert -87.95 <= restaurant["longitude"] <= -87.50
        assert restaurant["cuisine"] in CUISINES
        assert restaurant["neighborhood"] in NEIGHBORHOODS
        assert restaurant["price_category"] in PRICE_RANGES

        minimum_cost, maximum_cost = PRICE_RANGES[restaurant["price_category"]]
        assert type(restaurant["estimated_cost_per_person"]) is int
        assert (
            minimum_cost
            <= restaurant["estimated_cost_per_person"]
            <= maximum_cost
        )
        assert type(restaurant["vegetarian_available"]) is bool
        assert type(restaurant["vegan_available"]) is bool
        if restaurant["vegan_available"]:
            assert restaurant["vegetarian_available"]

        assert 1.0 <= restaurant["rating"] <= 5.0
        assert type(restaurant["review_count"]) is int
        assert restaurant["review_count"] >= 0

        opening_hours = restaurant["opening_hours"]
        assert set(opening_hours) == set(DAYS)
        assert sum(period is not None for period in opening_hours.values()) >= 6
        for period in opening_hours.values():
            if period is None:
                continue
            assert TIME_PATTERN.fullmatch(period["open"])
            assert TIME_PATTERN.fullmatch(period["close"])
            assert period["open"] < period["close"]

        transportation = restaurant["estimated_transportation"]
        assert set(transportation) == set(NEIGHBORHOODS)
        for estimate in transportation.values():
            assert estimate["estimate_type"] == "synthetic"
            assert estimate["straight_line_distance_km"] >= 0
            assert type(estimate["walking_minutes"]) is int
            assert type(estimate["public_transit_minutes"]) is int
            assert type(estimate["driving_minutes"]) is int
            assert estimate["walking_minutes"] > 0
            assert estimate["public_transit_minutes"] > 0
            assert estimate["driving_minutes"] > 0
