import pytest
from fastapi.testclient import TestClient

from bitecheck_api.main import app


client = TestClient(app)


def suggested_state() -> dict[str, object]:
    return {
        "filters": {
            "maximum_budget": 25,
            "vegetarian_required": True,
            "starting_area": "Illinois Tech",
            "maximum_travel_time": 30,
        },
        "sort_mode": "weighted",
        "travel_preference": "any",
        "theme_preference": None,
        "result_limit": None,
    }


@pytest.mark.parametrize(
    ("message", "intent"),
    (
        ("Only show walkable options.", "walkable_only"),
        ("Show me the cheapest one.", "cheapest"),
        ("Which has better vegetarian choices?", "vegetarian_quality"),
        ("Prioritize authenticity over distance.", "authenticity_priority"),
        ("Which restaurant has the most reliable reviews?", "review_reliability"),
        ("What are the common complaints?", "inspect_complaints"),
        ("Show all options.", "show_all"),
        ("Start over.", "reset"),
    ),
)
def test_supported_follow_ups_return_explicit_intents(
    message: str, intent: str
) -> None:
    response = client.post(
        "/restaurants/conversation",
        json={"message": message, "state": suggested_state()},
    )

    assert response.status_code == 200
    assert response.json()["intent"] == intent
    assert response.json()["transition_explanation"]


def test_walkable_follow_up_filters_by_selected_travel_mode() -> None:
    response = client.post(
        "/restaurants/conversation",
        json={
            "message": "Only show walkable options.",
            "state": suggested_state(),
        },
    )
    payload = response.json()

    assert payload["candidate_count_before_limit"] == 4
    assert payload["results"]["match_count"] == 4
    assert all(
        card["travel"]["selected_mode"] == "walking"
        for card in payload["results"]["recommendations"]
    )


def test_state_can_flow_through_a_multi_turn_sequence() -> None:
    walkable = client.post(
        "/restaurants/conversation",
        json={
            "message": "Only show walkable options.",
            "state": suggested_state(),
        },
    ).json()
    cheapest = client.post(
        "/restaurants/conversation",
        json={
            "message": "Now show the cheapest one.",
            "state": walkable["state"],
        },
    ).json()

    assert cheapest["state"]["travel_preference"] == "walkable"
    assert cheapest["state"]["sort_mode"] == "cheapest"
    assert cheapest["candidate_count_before_limit"] == 4
    assert cheapest["results"]["match_count"] == 1
    assert cheapest["results"]["recommendations"][0]["name"] == (
        "Silver Orchid Cafe"
    )


def test_theme_and_reliability_follow_ups_change_sort_state() -> None:
    vegetarian = client.post(
        "/restaurants/conversation",
        json={
            "message": "Better vegetarian choices",
            "state": suggested_state(),
        },
    ).json()
    reliable = client.post(
        "/restaurants/conversation",
        json={"message": "Most reliable reviews", "state": suggested_state()},
    ).json()

    assert vegetarian["state"]["theme_preference"] == "vegetarian_options"
    assert vegetarian["state"]["filters"]["vegetarian_required"] is True
    assert vegetarian["results"]["match_count"] == 1
    assert reliable["results"]["recommendations"][0]["name"] == (
        "North Sakura Kitchen"
    )


def test_walkable_requires_a_starting_area() -> None:
    response = client.post(
        "/restaurants/conversation",
        json={"message": "Only walkable options"},
    )

    assert response.status_code == 422
    assert "starting area is required" in response.json()["detail"][
        "message"
    ].lower()


def test_unsupported_follow_up_is_rejected_instead_of_guessed() -> None:
    response = client.post(
        "/restaurants/conversation",
        json={"message": "Find somewhere with live jazz", "state": suggested_state()},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "not supported" in detail["message"]
    assert len(detail["supported_examples"]) == 8


def test_reset_clears_filters_and_conversation_preferences() -> None:
    response = client.post(
        "/restaurants/conversation",
        json={"message": "Start over", "state": suggested_state()},
    )
    payload = response.json()

    assert payload["state"] == {
        "filters": {
            "cuisine": None,
            "maximum_budget": None,
            "vegetarian_required": False,
            "starting_area": None,
            "maximum_travel_time": None,
        },
        "sort_mode": "weighted",
        "travel_preference": "any",
        "theme_preference": None,
        "result_limit": None,
    }
    assert payload["results"]["match_count"] == 24
