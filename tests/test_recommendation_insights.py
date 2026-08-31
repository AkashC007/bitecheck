import json
from pathlib import Path
from typing import cast

from scripts.build_recommendation_insights import (
    DEFAULT_OUTPUT_PATH,
    build_recommendation_insights,
    write_recommendation_insights,
)


def load_committed_insights() -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads(DEFAULT_OUTPUT_PATH.read_text(encoding="utf-8")),
    )


def test_committed_insights_match_current_builder() -> None:
    assert load_committed_insights() == build_recommendation_insights()


def test_insights_cover_every_restaurant_and_review() -> None:
    payload = load_committed_insights()
    metadata = cast(dict[str, object], payload["metadata"])
    restaurants = cast(list[dict[str, object]], payload["restaurants"])

    assert metadata["restaurant_count"] == len(restaurants) == 24
    assert metadata["review_count"] == 288
    assert metadata["excluded_exact_duplicate_reviews"] == 24
    assert len({item["restaurant_id"] for item in restaurants}) == 24
    assert all(item["observation_count"] == 12 for item in restaurants)


def test_insights_limit_and_order_theme_signals() -> None:
    restaurants = cast(
        list[dict[str, object]], load_committed_insights()["restaurants"]
    )

    for restaurant in restaurants:
        for key in ("top_positive_themes", "top_negative_themes"):
            themes = cast(list[dict[str, object]], restaurant[key])
            assert 0 < len(themes) <= 3
            ordering = [
                (-cast(int, theme["mention_count"]), cast(str, theme["theme"]))
                for theme in themes
            ]
            assert ordering == sorted(ordering)


def test_latest_review_dates_are_fixed_and_iso_formatted() -> None:
    restaurants = cast(
        list[dict[str, object]], load_committed_insights()["restaurants"]
    )

    assert all(
        len(cast(str, item["latest_review_date"])) == 10
        and cast(str, item["latest_review_date"]) <= "2026-01-15"
        for item in restaurants
    )


def test_write_recommendation_insights_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    write_recommendation_insights(first)
    write_recommendation_insights(second)

    assert first.read_bytes() == second.read_bytes()
