from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bitecheck_api.main import app
from bitecheck_api.restaurants.insights import (
    JsonRecommendationInsightsRepository,
    get_recommendation_insights_repository,
)


client = TestClient(app)


def suggested_request() -> dict[str, object]:
    return {
        "filters": {
            "maximum_budget": 25,
            "vegetarian_required": True,
            "starting_area": "Illinois Tech",
            "maximum_travel_time": 30,
        }
    }


def test_recommendations_combine_every_card_signal() -> None:
    response = client.post("/restaurants/recommendations", json=suggested_request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_count"] == len(payload["recommendations"]) == 8
    assert payload["recommendations"][0]["name"] == "Little Sakura Kitchen"
    assert payload["recommendations"][0]["total_score"] == 79.2
    assert payload["assigned_categories"] == [
        "best_overall",
        "best_walkable",
        "best_public_transportation",
        "best_value",
        "most_consistently_recommended",
        "best_vegetarian_match",
        "hidden_gem",
        "mixed_reviews",
    ]

    for card in payload["recommendations"]:
        assert card["travel"]["starting_area"] == "Illinois Tech"
        assert len(card["top_positive_themes"]) == 3
        assert len(card["top_negative_themes"]) == 3
        assert card["review_confidence_score"] == card["ranking_factors"][
            "review_confidence"
        ]["score"]
        assert card["latest_review_date"] in card["data_freshness_label"]
        assert "synthetic" in payload["data_notice"].lower()


def test_recommendation_categories_have_one_winner_and_reasons() -> None:
    payload = client.post(
        "/restaurants/recommendations", json=suggested_request()
    ).json()
    badges = [
        badge
        for card in payload["recommendations"]
        for badge in card["categories"]
    ]

    assert {badge["category"] for badge in badges} == set(
        payload["assigned_categories"]
    )
    assert len(badges) == len(payload["assigned_categories"])
    assert all(badge["label"] and badge["reason"] for badge in badges)


def test_recommendations_remain_ranked_and_totals_reconcile() -> None:
    recommendations = client.post(
        "/restaurants/recommendations", json=suggested_request()
    ).json()["recommendations"]

    assert [card["total_score"] for card in recommendations] == sorted(
        (card["total_score"] for card in recommendations), reverse=True
    )
    for card in recommendations:
        assert sum(
            factor["contribution"] for factor in card["ranking_factors"].values()
        ) == pytest.approx(card["total_score"], abs=0.02)


def test_recommendations_without_origin_omit_travel_specific_categories() -> None:
    payload = client.post("/restaurants/recommendations", json={}).json()

    assert payload["match_count"] == 24
    assert all(card["travel"] is None for card in payload["recommendations"])
    assert "best_walkable" not in payload["assigned_categories"]
    assert "best_public_transportation" not in payload["assigned_categories"]


def test_recommendations_return_an_empty_success_when_filters_have_no_matches() -> None:
    response = client.post(
        "/restaurants/recommendations",
        json={"filters": {"maximum_budget": 1}},
    )

    assert response.status_code == 200
    assert response.json()["match_count"] == 0
    assert response.json()["recommendations"] == []
    assert response.json()["assigned_categories"] == []


@pytest.fixture
def unavailable_insights(tmp_path: Path) -> Iterator[None]:
    missing_path = tmp_path / "missing-insights.json"

    def override() -> JsonRecommendationInsightsRepository:
        return JsonRecommendationInsightsRepository(missing_path)

    app.dependency_overrides[get_recommendation_insights_repository] = override
    try:
        yield
    finally:
        app.dependency_overrides.clear()


def test_recommendations_return_safe_503_for_missing_insights(
    unavailable_insights: None,
) -> None:
    response = client.post("/restaurants/recommendations", json=suggested_request())

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Recommendation insights are temporarily unavailable."
    }
