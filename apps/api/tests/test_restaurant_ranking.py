import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from bitecheck_api.main import app
from bitecheck_api.restaurants.models import RankingWeights
from bitecheck_api.restaurants.ranking import (
    RankingConfigurationError,
    load_ranking_weights,
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


def test_default_ranking_configuration_is_valid_and_sums_to_one() -> None:
    weights = load_ranking_weights()

    assert sum(weights.model_dump().values()) == pytest.approx(1.0)
    assert weights.review_confidence == 0.2


@pytest.mark.parametrize(
    "values",
    (
        {
            "cuisine_match": 0.2,
            "dietary_match": 0.15,
            "budget_match": 0.15,
            "travel_convenience": 0.2,
            "rating": 0.09,
            "review_confidence": 0.2,
        },
        {
            "cuisine_match": 0,
            "dietary_match": 0,
            "budget_match": 0,
            "travel_convenience": 0,
            "rating": 0,
            "review_confidence": 1,
        },
    ),
)
def test_ranking_weights_reject_invalid_totals_or_no_active_baseline(
    values: dict[str, float],
) -> None:
    with pytest.raises(ValidationError):
        RankingWeights(**values)


def test_ranking_configuration_reports_missing_and_invalid_files(
    tmp_path: Path,
) -> None:
    with pytest.raises(RankingConfigurationError):
        load_ranking_weights(tmp_path / "missing.json")

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(json.dumps({"weights": {}}), encoding="utf-8")
    with pytest.raises(RankingConfigurationError):
        load_ranking_weights(invalid_path)


def test_ranking_endpoint_orders_suggested_matches() -> None:
    response = client.post("/restaurants/rank", json=suggested_request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_count"] == 9
    assert payload["rankings"][0]["rank"] == 1
    assert payload["rankings"][0]["total_score"] > 0
    assert [item["total_score"] for item in payload["rankings"]] == sorted(
        (item["total_score"] for item in payload["rankings"]),
        reverse=True,
    )


def test_factor_contributions_reconcile_to_total_score() -> None:
    payload = client.post("/restaurants/rank", json=suggested_request()).json()

    for restaurant in payload["rankings"]:
        factors = restaurant["factors"].values()
        assert sum(factor["contribution"] for factor in factors) == pytest.approx(
            restaurant["total_score"],
            abs=0.02,
        )
        assert sum(
            factor["effective_weight"]
            for factor in factors
            if factor["status"] == "active"
        ) == pytest.approx(1.0, abs=0.00001)


def test_review_confidence_is_active_and_explained_as_evidence_quality() -> None:
    payload = client.post("/restaurants/rank", json=suggested_request()).json()
    review_factor = payload["rankings"][0]["factors"]["review_confidence"]

    assert payload["unavailable_factors"] == []
    assert review_factor["status"] == "active"
    assert 0 <= review_factor["score"] <= 100
    assert review_factor["effective_weight"] > 0
    assert review_factor["contribution"] > 0
    assert "not truth" in review_factor["explanation"]


def test_unrequested_preferences_are_not_treated_as_perfect_matches() -> None:
    payload = client.post("/restaurants/rank", json={}).json()
    factors = payload["rankings"][0]["factors"]

    assert payload["match_count"] == 24
    assert factors["cuisine_match"]["status"] == "not_applicable"
    assert factors["dietary_match"]["status"] == "not_applicable"
    assert factors["budget_match"]["status"] == "not_applicable"
    assert factors["travel_convenience"]["status"] == "not_applicable"
    assert factors["rating"]["effective_weight"] == pytest.approx(1 / 3, abs=0.000001)
    assert factors["review_confidence"]["effective_weight"] == pytest.approx(
        2 / 3, abs=0.000001
    )


def test_equal_scores_share_a_rank_and_preserve_source_order() -> None:
    rating_only_weights = {
        "cuisine_match": 0,
        "dietary_match": 0,
        "budget_match": 0,
        "travel_convenience": 0,
        "rating": 1,
        "review_confidence": 0,
    }
    payload = client.post(
        "/restaurants/rank", json={"weights": rating_only_weights}
    ).json()
    rankings = payload["rankings"]
    tied_pair = next(
        (left, right)
        for left, right in zip(rankings, rankings[1:], strict=False)
        if left["total_score"] == right["total_score"]
    )

    assert tied_pair[0]["rank"] == tied_pair[1]["rank"]
    assert tied_pair[0]["restaurant_id"] < tied_pair[1]["restaurant_id"]


def test_ranking_endpoint_accepts_valid_custom_weights() -> None:
    weights = load_ranking_weights().model_dump()
    weights.update(
        {
            "cuisine_match": 0.1,
            "travel_convenience": 0.1,
            "rating": 0.3,
        }
    )
    response = client.post(
        "/restaurants/rank",
        json={**suggested_request(), "weights": weights},
    )

    assert response.status_code == 200
    assert response.json()["configured_weights"] == weights


def test_ranking_endpoint_returns_empty_success_for_no_matches() -> None:
    response = client.post(
        "/restaurants/rank",
        json={"filters": {"maximum_budget": 1}},
    )

    assert response.status_code == 200
    assert response.json()["match_count"] == 0
    assert response.json()["rankings"] == []


def test_ranking_endpoint_rejects_invalid_filters_and_weights() -> None:
    invalid_filter = client.post(
        "/restaurants/rank",
        json={"filters": {"cuisine": "Martian"}},
    )
    invalid_weights = client.post(
        "/restaurants/rank",
        json={
            "weights": {
                "cuisine_match": 1,
                "dietary_match": 1,
                "budget_match": 1,
                "travel_convenience": 1,
                "rating": 1,
                "review_confidence": 1,
            }
        },
    )

    assert invalid_filter.status_code == 422
    assert invalid_weights.status_code == 422
