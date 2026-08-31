from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bitecheck_api.main import app
from bitecheck_api.restaurants.repository import (
    DEFAULT_DATASET_PATH,
    JsonRestaurantRepository,
    get_restaurant_repository,
)


client = TestClient(app)


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


def test_search_without_filters_returns_dataset_in_stable_order() -> None:
    response = client.get("/restaurants/search")

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_count"] == 24
    assert payload["applied_filters"] == {
        "cuisine": None,
        "maximum_budget": None,
        "vegetarian_required": False,
        "starting_area": None,
        "maximum_travel_time": None,
    }
    source_records = JsonRestaurantRepository(DEFAULT_DATASET_PATH).list_restaurants()
    assert [restaurant["restaurant_id"] for restaurant in payload["restaurants"]] == [
        restaurant.restaurant_id for restaurant in source_records
    ]
    assert all(
        restaurant["latest_inspection"]["result"]
        in {"Pass", "Pass w/ Conditions"}
        for restaurant in payload["restaurants"]
    )


def test_search_matches_cuisine_without_case_sensitivity() -> None:
    response = client.get("/restaurants/search", params={"cuisine": "chinese"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_count"] == 3
    assert payload["applied_filters"]["cuisine"] == "Chinese"
    source_records = JsonRestaurantRepository(DEFAULT_DATASET_PATH).list_restaurants()
    assert {
        restaurant["restaurant_id"] for restaurant in payload["restaurants"]
    } == {
        restaurant.restaurant_id
        for restaurant in source_records
        if restaurant.cuisine == "Chinese"
    }
    assert all(
        restaurant["cuisine"] == "Chinese"
        for restaurant in payload["restaurants"]
    )


def test_search_applies_maximum_budget_inclusively() -> None:
    response = client.get("/restaurants/search", params={"maximum_budget": 18})

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_count"] == 8
    assert all(
        restaurant["estimated_cost_per_person"] <= 18
        for restaurant in payload["restaurants"]
    )


def test_search_requires_a_vegetarian_option_when_requested() -> None:
    response = client.get(
        "/restaurants/search",
        params={"vegetarian_required": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_count"] == 20
    assert all(
        restaurant["vegetarian_available"]
        for restaurant in payload["restaurants"]
    )


def test_search_uses_fastest_non_driving_travel_time() -> None:
    response = client.get(
        "/restaurants/search",
        params={
            "starting_area": "illinois tech",
            "maximum_travel_time": 30,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_count"] == 21
    assert payload["applied_filters"]["starting_area"] == "Illinois Tech"
    assert all(
        restaurant["travel"]["minutes"] <= 30
        and restaurant["travel"]["mode"] in {"walking", "public_transit"}
        for restaurant in payload["restaurants"]
    )


def test_search_combines_all_filters_with_and_logic() -> None:
    response = client.get(
        "/restaurants/search",
        params={
            "cuisine": "chinese",
            "maximum_budget": 25,
            "vegetarian_required": True,
            "starting_area": "Illinois Tech",
            "maximum_travel_time": 30,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_count"] == len(payload["restaurants"])
    assert payload["match_count"] > 0
    assert all(
        restaurant["cuisine"] == "Chinese"
        and restaurant["estimated_cost_per_person"] <= 25
        and restaurant["vegetarian_available"]
        and restaurant["travel"]["minutes"] <= 30
        for restaurant in payload["restaurants"]
    )


def test_search_returns_empty_success_response_when_nothing_matches() -> None:
    response = client.get("/restaurants/search", params={"maximum_budget": 1})

    assert response.status_code == 200
    assert response.json()["match_count"] == 0
    assert response.json()["restaurants"] == []


def test_search_requires_starting_area_for_travel_limit() -> None:
    response = client.get(
        "/restaurants/search",
        params={"maximum_travel_time": 30},
    )

    assert response.status_code == 422
    assert "starting_area is required" in response.json()["detail"][0]["msg"]


@pytest.mark.parametrize(
    ("field", "value"),
    (("cuisine", "Martian"), ("starting_area", "Moon Base")),
)
def test_search_explains_unsupported_filter_values(field: str, value: str) -> None:
    response = client.get("/restaurants/search", params={field: value})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["field"] == field
    assert value in detail["message"]
    assert detail["allowed_values"]


def test_search_rejects_unknown_query_parameters() -> None:
    response = client.get("/restaurants/search", params={"unknown": "value"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_search_hides_internal_details_when_dataset_is_unavailable(
    unavailable_restaurant_data: None,
) -> None:
    response = client.get("/restaurants/search")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Restaurant data is temporarily unavailable."
    }
