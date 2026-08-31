import json
from pathlib import Path
from typing import cast

from scripts.analyze_review_themes import (
    DEFAULT_OUTPUT_PATH,
    THEME_TERMS,
    analyze_dataset,
    analyze_review,
    normalize_review_text,
    write_analysis,
)
from scripts.generate_review_data import DEFAULT_OUTPUT_PATH as REVIEW_DATA_PATH


def load_committed_analysis() -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads(DEFAULT_OUTPUT_PATH.read_text(encoding="utf-8")),
    )


def test_normalize_review_text_standardizes_case_punctuation_and_spacing() -> None:
    assert normalize_review_text("  Fresh,\tFLAVORFUL food!! ") == (
        "fresh flavorful food"
    )


def test_analyzer_extracts_the_roadmap_example() -> None:
    result = analyze_review(
        "example",
        "restaurant",
        "source",
        "The noodles were excellent, but the service was slow.",
    )
    predictions = {
        (aspect["theme"], aspect["sentiment"]) for aspect in result["aspects"]
    }

    assert result["overall_sentiment"] == "mixed"
    assert predictions == {
        ("specific_dishes", "positive"),
        ("food_quality", "positive"),
        ("service", "negative"),
        ("waiting_time", "negative"),
    }


def test_analyzer_returns_neutral_when_no_theme_is_recognized() -> None:
    result = analyze_review("id", "restaurant", "source", "It was okay.")

    assert result["overall_sentiment"] == "neutral"
    assert result["theme_count"] == 0
    assert result["aspects"] == []


def test_committed_analysis_matches_current_rules() -> None:
    assert load_committed_analysis() == analyze_dataset()


def test_analysis_processes_every_review_and_covers_every_theme() -> None:
    result = load_committed_analysis()
    metadata = cast(dict[str, object], result["metadata"])
    reviews = cast(list[dict[str, object]], result["reviews"])
    summary = cast(dict[str, dict[str, object]], result["theme_summary"])

    assert metadata["input_record_count"] == 288
    assert metadata["analyzed_record_count"] == 288
    assert len(reviews) == 288
    assert set(summary) == set(THEME_TERMS)
    assert all(cast(int, values["mention_count"]) > 0 for values in summary.values())


def test_theme_summary_counts_reconcile_to_review_predictions() -> None:
    result = load_committed_analysis()
    reviews = cast(list[dict[str, object]], result["reviews"])
    summary = cast(dict[str, dict[str, object]], result["theme_summary"])

    predicted_count = sum(cast(int, review["theme_count"]) for review in reviews)
    summary_count = sum(cast(int, values["mention_count"]) for values in summary.values())
    assert predicted_count == summary_count


def test_exact_duplicate_reviews_receive_identical_predictions() -> None:
    source_payload = cast(
        dict[str, object], json.loads(REVIEW_DATA_PATH.read_text(encoding="utf-8"))
    )
    source_reviews = cast(list[dict[str, object]], source_payload["reviews"])
    analysis = cast(list[dict[str, object]], load_committed_analysis()["reviews"])
    by_id = {cast(str, item["review_id"]): item for item in analysis}

    for review in source_reviews:
        parent_id = review["duplicate_of_review_id"]
        if parent_id is not None:
            assert by_id[cast(str, review["review_id"])]["aspects"] == by_id[
                cast(str, parent_id)
            ]["aspects"]


def test_evaluation_metrics_meet_rule_based_baseline() -> None:
    evaluation = cast(dict[str, float], load_committed_analysis()["evaluation"])

    assert evaluation["precision"] >= 0.95
    assert evaluation["recall"] >= 0.95
    assert evaluation["f1"] >= 0.95


def test_write_analysis_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    write_analysis(first)
    write_analysis(second)

    assert first.read_bytes() == second.read_bytes()
