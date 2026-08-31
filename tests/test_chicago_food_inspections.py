import json
from pathlib import Path
from typing import cast

import pytest

from scripts.ingest_chicago_food_inspections import (
    ACCEPTED_LATEST_RESULTS,
    AREA_CENTERS,
    DATASET_ID,
    DEFAULT_OUTPUT_PATH,
    SNAPSHOT_DATE,
    InspectionRow,
    Snapshot,
    build_snapshot,
)


def _row(
    *,
    license_number: int,
    name: str,
    latitude: float,
    longitude: float,
    inspection_date: str = "2026-05-01T00:00:00.000",
    result: str = "Pass",
    inspection_id: int | None = None,
) -> InspectionRow:
    return {
        "inspection_id": str(inspection_id or license_number * 10),
        "dba_name": name.upper(),
        "aka_name": name.upper(),
        "license_": str(license_number),
        "facility_type": "Restaurant",
        "risk": "Risk 1 (High)",
        "address": f"{license_number} TEST ST",
        "city": "CHICAGO",
        "state": "IL",
        "zip": "60601",
        "inspection_date": inspection_date,
        "inspection_type": "Canvass",
        "results": result,
        "latitude": str(latitude),
        "longitude": str(longitude),
    }


def _one_valid_row_per_area() -> list[InspectionRow]:
    return [
        _row(
            license_number=index,
            name=f"Restaurant {index}",
            latitude=center["latitude"],
            longitude=center["longitude"],
        )
        for index, center in enumerate(AREA_CENTERS.values(), start=1)
    ]


def test_build_snapshot_balances_areas_and_keeps_latest_history() -> None:
    rows = _one_valid_row_per_area()
    first_center = next(iter(AREA_CENTERS.values()))
    rows.append(
        _row(
            license_number=1,
            name="Restaurant 1",
            latitude=first_center["latitude"],
            longitude=first_center["longitude"],
            inspection_date="2025-01-01T00:00:00.000",
            result="Fail",
            inspection_id=1,
        )
    )
    rows.append(rows[-1].copy())

    snapshot = build_snapshot(rows, target_count=7)

    assert {row["neighborhood"] for row in snapshot["restaurants"]} == set(
        AREA_CENTERS
    )
    first = snapshot["restaurants"][0]
    assert first["latest_inspection"]["inspection_date"] == "2026-05-01"
    assert first["latest_inspection"]["result"] == "Pass"
    assert first["inspection_history"]["inspection_count"] == 2
    assert first["inspection_history"]["fail_count"] == 1


def test_build_snapshot_excludes_a_license_when_latest_result_failed() -> None:
    rows = _one_valid_row_per_area()
    first_center = next(iter(AREA_CENTERS.values()))
    rows.extend(
        (
            _row(
                license_number=50,
                name="Old Pass Latest Fail",
                latitude=first_center["latitude"],
                longitude=first_center["longitude"],
                inspection_date="2025-01-01T00:00:00.000",
                result="Pass",
                inspection_id=500,
            ),
            _row(
                license_number=50,
                name="Old Pass Latest Fail",
                latitude=first_center["latitude"],
                longitude=first_center["longitude"],
                inspection_date="2026-06-01T00:00:00.000",
                result="Fail",
                inspection_id=501,
            ),
        )
    )

    snapshot = build_snapshot(rows, target_count=7)

    assert all(
        restaurant["license_number"] != "50"
        for restaurant in snapshot["restaurants"]
    )


def test_build_snapshot_rejects_non_positive_target() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        build_snapshot([], target_count=0)


def test_committed_snapshot_has_documented_real_source() -> None:
    snapshot = cast(
        Snapshot,
        json.loads(Path(DEFAULT_OUTPUT_PATH).read_text(encoding="utf-8")),
    )

    assert snapshot["metadata"]["dataset_id"] == DATASET_ID
    assert snapshot["metadata"]["snapshot_date"] == SNAPSHOT_DATE
    assert snapshot["metadata"]["attribution"] == "City of Chicago"
    assert snapshot["metadata"]["selected_record_count"] == 24
    assert len(snapshot["restaurants"]) == 24
    assert len(
        {restaurant["restaurant_id"] for restaurant in snapshot["restaurants"]}
    ) == 24
    assert all(
        restaurant["latest_inspection"]["result"] in ACCEPTED_LATEST_RESULTS
        for restaurant in snapshot["restaurants"]
    )
