import pytest
from fastapi.testclient import TestClient

from bitecheck_api.main import app
from bitecheck_api.restaurants.parser import (
    NaturalLanguageParseError,
    RuleBasedRestaurantRequestParser,
    normalize_text,
)


client = TestClient(app)
parser = RuleBasedRestaurantRequestParser()


def test_normalize_text_standardizes_case_unicode_and_whitespace() -> None:
    assert normalize_text("  Find\tＣＨＩＮＥＳＥ\nFood  ") == "find chinese food"


def test_parser_converts_the_roadmap_example() -> None:
    result = parser.parse(
        "Find Chinese food under $25 with vegetarian options."
    )

    assert result.model_dump() == {
        "cuisine": "Chinese",
        "maximum_budget": 25,
        "vegetarian_required": True,
        "starting_area": None,
        "maximum_travel_time": None,
    }


def test_parser_converts_the_full_product_example() -> None:
    result = parser.parse(
        "Find a good Chinese restaurant near Illinois Tech with vegetarian "
        "options, under $25, reachable within 30 minutes by walking or public "
        "transportation."
    )

    assert result.model_dump() == {
        "cuisine": "Chinese",
        "maximum_budget": 25,
        "vegetarian_required": True,
        "starting_area": "Illinois Tech",
        "maximum_travel_time": 30,
    }


@pytest.mark.parametrize(
    ("phrase", "expected"),
    (
        ("American food", "American"),
        ("Chinese food", "Chinese"),
        ("Ethiopian food", "Ethiopian"),
        ("Indian food", "Indian"),
        ("Italian food", "Italian"),
        ("Japanese food", "Japanese"),
        ("Korean food", "Korean"),
        ("Mediterranean food", "Mediterranean"),
        ("Mexican food", "Mexican"),
        ("Thai food", "Thai"),
    ),
)
def test_parser_recognizes_every_supported_cuisine(
    phrase: str,
    expected: str,
) -> None:
    assert parser.parse(phrase).cuisine == expected


@pytest.mark.parametrize(
    ("phrase", "expected"),
    (
        ("near IIT", "Illinois Tech"),
        ("near Illinois Institute of Technology", "Illinois Tech"),
        ("in Chinatown", "Chinatown"),
        ("around the Loop", "Chicago Loop"),
        ("from Hyde Park", "Hyde Park"),
        ("starting in Bridgeport", "Bridgeport"),
        ("from Lake View", "Lakeview"),
        ("near River North", "River North"),
    ),
)
def test_parser_recognizes_area_names_and_aliases(
    phrase: str,
    expected: str,
) -> None:
    assert parser.parse(phrase).starting_area == expected


def test_parser_does_not_confuse_travel_minutes_with_budget() -> None:
    result = parser.parse("Thai near Hyde Park under 30 minutes")

    assert result.maximum_budget is None
    assert result.maximum_travel_time == 30


@pytest.mark.parametrize(
    "phrase",
    ("no vegetarian food needed", "vegetarian options are optional"),
)
def test_parser_respects_negative_vegetarian_phrases(phrase: str) -> None:
    assert parser.parse(phrase).vegetarian_required is False


def test_parser_does_not_weaken_a_vegan_request_to_vegetarian() -> None:
    assert parser.parse("I need vegan food").vegetarian_required is False


def test_parser_returns_empty_filters_for_unrecognized_preferences() -> None:
    result = parser.parse("Find a good authentic restaurant")

    assert result.model_dump() == {
        "cuisine": None,
        "maximum_budget": None,
        "vegetarian_required": False,
        "starting_area": None,
        "maximum_travel_time": None,
    }


@pytest.mark.parametrize(
    ("text", "field"),
    (
        ("Chinese or Thai", "cuisine"),
        ("near Hyde Park or Lakeview", "starting_area"),
        ("under $20 or $30", "maximum_budget"),
        (
            "near IIT within 20 minutes or under 30 minutes",
            "maximum_travel_time",
        ),
        ("within 30 minutes", "starting_area"),
        ("under $0", "maximum_budget"),
        ("near IIT within 0 minutes", "maximum_travel_time"),
    ),
)
def test_parser_rejects_unsafe_or_incomplete_interpretations(
    text: str,
    field: str,
) -> None:
    with pytest.raises(NaturalLanguageParseError) as error:
        parser.parse(text)

    assert error.value.field == field


def test_parse_endpoint_returns_structured_filters() -> None:
    response = client.post(
        "/restaurants/parse",
        json={
            "text": (
                "Japanese near IIT, veggie, up to 25 bucks, within 30 mins"
            )
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "cuisine": "Japanese",
        "maximum_budget": 25,
        "vegetarian_required": True,
        "starting_area": "Illinois Tech",
        "maximum_travel_time": 30,
    }


def test_parse_endpoint_returns_explainable_ambiguity_error() -> None:
    response = client.post(
        "/restaurants/parse",
        json={"text": "Chinese or Thai near IIT"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == {
        "field": "cuisine",
        "message": (
            "The request mentions multiple cuisine values. Please choose one."
        ),
        "candidates": ["Chinese", "Thai"],
    }


@pytest.mark.parametrize(
    "payload",
    (
        {"text": "   "},
        {"text": "Thai", "unexpected": True},
        {},
    ),
)
def test_parse_endpoint_rejects_invalid_request_bodies(
    payload: dict[str, object],
) -> None:
    response = client.post("/restaurants/parse", json=payload)

    assert response.status_code == 422
