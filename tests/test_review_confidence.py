import json
from pathlib import Path
from typing import cast

import pytest

from scripts.calculate_review_confidence import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_OUTPUT_PATH,
    calculate_confidence_dataset,
    write_confidence_dataset,
)


EXPECTED_COMPONENTS = {
    "cross_source_agreement",
    "observation_volume",
    "review_recency",
    "source_diversity",
    "review_specificity",
    "branch_match_confidence",
    "rating_consistency",
}
EXPECTED_PENALTIES = {
    "exact_duplicates",
    "repetitive_language",
    "suspicious_bursts",
    "missing_data",
}


def load_committed_confidence() -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads(DEFAULT_OUTPUT_PATH.read_text(encoding="utf-8")),
    )


def confidence_records() -> list[dict[str, object]]:
    return cast(list[dict[str, object]], load_committed_confidence()["restaurants"])


def test_committed_confidence_matches_current_methodology() -> None:
    assert load_committed_confidence() == calculate_confidence_dataset()


def test_configuration_contains_every_factor_and_sums_to_one() -> None:
    config = cast(
        dict[str, object], json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    )
    weights = cast(dict[str, float], config["component_weights"])
    penalties = cast(dict[str, float], config["maximum_penalties"])

    assert set(weights) == EXPECTED_COMPONENTS
    assert sum(weights.values()) == pytest.approx(1.0)
    assert set(penalties) == EXPECTED_PENALTIES
    assert all(value >= 0 for value in penalties.values())


def test_every_restaurant_has_a_bounded_explainable_score() -> None:
    payload = load_committed_confidence()
    metadata = cast(dict[str, object], payload["metadata"])
    records = confidence_records()

    assert metadata["not_a_truth_score"] is True
    assert metadata["restaurant_count"] == len(records) == 24
    assert metadata["review_count"] == 288
    assert len({record["restaurant_id"] for record in records}) == 24
    for record in records:
        assert 0 <= cast(float, record["review_confidence_score"]) <= 100
        assert record["confidence_band"] in {"low", "medium", "high"}
        assert "not a truth" in cast(str, record["interpretation"])


def test_components_and_penalties_reconcile_to_final_scores() -> None:
    for record in confidence_records():
        components = cast(dict[str, dict[str, object]], record["components"])
        penalties = cast(dict[str, dict[str, object]], record["penalties"])
        contribution_total = sum(
            cast(float, component["contribution"])
            for component in components.values()
        )
        penalty_total = sum(
            cast(float, penalty["penalty"]) for penalty in penalties.values()
        )

        assert set(components) == EXPECTED_COMPONENTS
        assert set(penalties) == EXPECTED_PENALTIES
        assert contribution_total == pytest.approx(
            cast(float, record["base_score"]), abs=0.02
        )
        assert penalty_total == pytest.approx(
            cast(float, record["total_penalty"]), abs=0.02
        )
        assert cast(float, record["review_confidence_score"]) == pytest.approx(
            max(
                0,
                cast(float, record["base_score"])
                - cast(float, record["total_penalty"]),
            ),
            abs=0.02,
        )


def test_component_contributions_use_configured_weights() -> None:
    for record in confidence_records():
        components = cast(dict[str, dict[str, object]], record["components"])
        for component in components.values():
            assert cast(float, component["contribution"]) == pytest.approx(
                cast(float, component["score"])
                * cast(float, component["weight"]),
                abs=0.01,
            )


def test_controlled_bursts_receive_the_suspicious_burst_penalty() -> None:
    records = confidence_records()
    penalties = [
        cast(dict[str, dict[str, object]], record["penalties"])[
            "suspicious_bursts"
        ]["penalty"]
        for record in records
    ]

    assert penalties.count(3.33) == 6
    assert penalties.count(0.0) == len(records) - 6


def test_complete_branch_and_source_data_receive_full_component_scores() -> None:
    for record in confidence_records():
        components = cast(dict[str, dict[str, object]], record["components"])
        assert components["branch_match_confidence"]["score"] == 100
        assert components["source_diversity"]["score"] == 100


def test_write_confidence_dataset_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    write_confidence_dataset(first)
    write_confidence_dataset(second)

    assert first.read_bytes() == second.read_bytes()
