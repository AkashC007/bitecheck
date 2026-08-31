from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from bitecheck_api.main import app
from bitecheck_api.restaurants.models import (
    TransportationEstimate,
    TravelCategoryThresholds,
)
from bitecheck_api.restaurants.repository import (
    JsonRestaurantRepository,
    get_restaurant_repository,
)
from bitecheck_api.restaurants.travel import categorize_travel


client = TestClient(app)


def estimate(
    walking: int,
    transit: int,
    driving: int,
) -> TransportationEstimate:
    return TransportationEstimate(
        straight_line_distance_km=1,
        walking_minutes=walking,
        public_transit_minutes=transit,
        driving_minutes=driving,
        estimate_type="synthetic",
    )


@pytest.mark.parametrize(
    ("travel", "category", "mode", "minutes"),
    (
        (estimate(15, 10, 5), "walkable", "walking", 15),
        (estimate(16, 10, 5), "comfortable_walk", "walking", 16),
        (estimate(25, 10, 5), "comfortable_walk", "walking", 25),
        (estimate(26, 30, 10), "easy_public_transit", "public_transit", 30),
        (estimate(60, 31, 10), "longer_public_transit", "public_transit", 31),
        (estimate(60, 50, 10), "longer_public_transit", "public_transit", 50),
        (estimate(60, 51, 20), "easy_drive", "driving", 20),
        (estimate(60, 51, 21), "inconvenient", "driving", 21),
    ),
)
def test_categorize_travel_applies_boundaries_in_priority_order(
    travel: TransportationEstimate,
    category: str,
    mode: str,
    minutes: int,
) -> None:
    decision = categorize_travel(travel, TravelCategoryThresholds())

    assert decision.category == category
    assert decision.selected_mode == mode
    assert decision.selected_minutes == minutes


def test_categorize_travel_respects_user_limit_for_each_mode() -> None:
    thresholds = TravelCategoryThresholds(maximum_acceptable_minutes=10)

    decision = categorize_travel(estimate(15, 9, 5), thresholds)

    assert decision.category == "easy_public_transit"
    assert decision.selected_minutes == 9


def test_categorize_travel_supports_custom_thresholds() -> None:
    thresholds = TravelCategoryThresholds(
        walkable_max_minutes=20,
        comfortable_walk_max_minutes=30,
    )

    assert categorize_travel(estimate(19, 10, 5), thresholds).category == "walkable"


def test_inconvenient_tie_uses_stable_mode_order() -> None:
    decision = categorize_travel(estimate(60, 60, 60), TravelCategoryThresholds())

    assert decision.category == "inconvenient"
    assert decision.selected_mode == "walking"
    assert "fastest estimate" in decision.explanation


@pytest.mark.parametrize(
    "values",
    (
        {"walkable_max_minutes": 20, "comfortable_walk_max_minutes": 19},
        {"easy_transit_max_minutes": 40, "longer_transit_max_minutes": 39},
    ),
)
def test_threshold_model_rejects_reversed_ranges(values: dict[str, int]) -> None:
    with pytest.raises(ValidationError):
        TravelCategoryThresholds(**values)


def test_travel_category_endpoint_returns_all_restaurants_and_counts() -> None:
    response = client.get(
        "/restaurants/travel-categories",
        params={"starting_area": "illinois tech"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["starting_area"] == "Illinois Tech"
    assert payload["restaurant_count"] == 24
    assert set(payload["category_counts"]) == {
        "walkable",
        "comfortable_walk",
        "easy_public_transit",
        "longer_public_transit",
        "easy_drive",
        "inconvenient",
    }
    assert sum(payload["category_counts"].values()) == 24
    assert all(
        item["restaurant_id"].startswith("CHI-COC-")
        for item in payload["restaurants"]
    )


def test_travel_category_endpoint_accepts_custom_user_limit() -> None:
    response = client.get(
        "/restaurants/travel-categories",
        params={
            "starting_area": "Illinois Tech",
            "maximum_acceptable_minutes": 10,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["thresholds"]["maximum_acceptable_minutes"] == 10
    assert payload["category_counts"]["inconvenient"] > 0
    assert sum(payload["category_counts"].values()) == 24


@pytest.mark.parametrize(
    "params",
    (
        {"starting_area": "Moon Base"},
        {
            "starting_area": "Illinois Tech",
            "walkable_max_minutes": 30,
            "comfortable_walk_max_minutes": 20,
        },
        {"starting_area": "Illinois Tech", "unknown": "value"},
    ),
)
def test_travel_category_endpoint_rejects_invalid_queries(
    params: dict[str, str | int],
) -> None:
    response = client.get("/restaurants/travel-categories", params=params)

    assert response.status_code == 422


@pytest.fixture
def unavailable_restaurant_data(tmp_path: Path) -> Iterator[None]:
    missing_dataset = tmp_path / "missing-restaurants.json"

    def override_repository() -> JsonRestaurantRepository:
        return JsonRestaurantRepository(missing_dataset)

    app.dependency_overrides[get_restaurant_repository] = override_repository
    try:
        yield
    finally:
        app.dependency_overrides.clear()


def test_travel_category_endpoint_hides_data_errors(
    unavailable_restaurant_data: None,
) -> None:
    response = client.get(
        "/restaurants/travel-categories",
        params={"starting_area": "Illinois Tech"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Restaurant data is temporarily unavailable."
    }
