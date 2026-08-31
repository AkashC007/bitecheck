from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from bitecheck_api.main import app
from bitecheck_api.restaurants.inspection_explorer import (
    InspectionProviderError,
    SourceInspection,
    build_chicago_query,
    get_inspection_provider,
    parse_source_rows,
)
from bitecheck_api.restaurants.models import InspectionExplorerRequest


client = TestClient(app)


def source_inspection(
    *,
    inspection_id: str,
    license_number: str,
    name: str,
    inspection_date: str,
    result: str,
    latitude: float = 41.8781,
    longitude: float = -87.6298,
) -> SourceInspection:
    return SourceInspection.model_validate(
        {
            "inspection_id": inspection_id,
            "dba_name": name,
            "aka_name": name,
            "license_": license_number,
            "facility_type": "Restaurant",
            "risk": "Risk 1 (High)",
            "address": "100 TEST ST",
            "city": "CHICAGO",
            "state": "IL",
            "zip": "60601",
            "inspection_date": inspection_date,
            "inspection_type": "Canvass",
            "results": result,
            "latitude": latitude,
            "longitude": longitude,
        }
    )


class FakeInspectionProvider:
    async def fetch(
        self, request: InspectionExplorerRequest
    ) -> tuple[SourceInspection, ...]:
        del request
        return (
            source_inspection(
                inspection_id="3",
                license_number="10",
                name="CURRENT CAFE",
                inspection_date="2026-08-29T00:00:00.000",
                result="Pass w/ Conditions",
                latitude=41.879,
            ),
            source_inspection(
                inspection_id="2",
                license_number="10",
                name="CURRENT CAFE",
                inspection_date="2025-08-29T00:00:00.000",
                result="Fail",
                latitude=41.879,
            ),
            source_inspection(
                inspection_id="1",
                license_number="20",
                name="SECOND CAFE",
                inspection_date="2026-08-28T00:00:00.000",
                result="Pass",
                latitude=41.89,
            ),
        )


class FailingInspectionProvider:
    async def fetch(
        self, request: InspectionExplorerRequest
    ) -> tuple[SourceInspection, ...]:
        del request
        raise InspectionProviderError("source unavailable")


@pytest.fixture
def fake_provider() -> Iterator[None]:
    app.dependency_overrides[get_inspection_provider] = FakeInspectionProvider
    try:
        yield
    finally:
        app.dependency_overrides.clear()


def test_query_targets_restaurants_location_and_safe_text() -> None:
    query = build_chicago_query(
        InspectionExplorerRequest(
            latitude=41.8781,
            longitude=-87.6298,
            radius_km=2,
            query="Joe's Cafe",
        )
    )

    assert "within_circle(location,41.878100,-87.629800,2000)" in query["$where"]
    assert "joe''s cafe" in query["$where"]
    assert "facility_type" in query["$where"]
    assert query["$order"] == "inspection_date desc,inspection_id desc"


def test_parser_skips_invalid_external_rows() -> None:
    valid = source_inspection(
        inspection_id="1",
        license_number="10",
        name="VALID CAFE",
        inspection_date="2026-08-29T00:00:00.000",
        result="Pass",
    ).model_dump(mode="json", by_alias=True)

    rows = parse_source_rows([valid, {"inspection_id": "missing fields"}])

    assert len(rows) == 1
    assert rows[0].dba_name == "VALID CAFE"


def test_live_explorer_deduplicates_sorts_and_summarizes(
    fake_provider: None,
) -> None:
    response = client.post(
        "/restaurants/inspections/explore",
        json={"latitude": 41.8781, "longitude": -87.6298, "radius_km": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_record_count"] == 3
    assert payload["restaurant_count"] == 2
    assert payload["restaurants"][0]["name"] == "CURRENT CAFE"
    assert payload["restaurants"][0]["distance_km"] == 0.1
    assert payload["restaurants"][0]["attention_level"] == "conditions_noted"
    assert payload["restaurants"][0]["history"] == {
        "records_in_query": 2,
        "pass_count": 0,
        "conditions_count": 1,
        "fail_count": 1,
        "other_count": 0,
    }


def test_live_explorer_filters_on_latest_result(fake_provider: None) -> None:
    response = client.post(
        "/restaurants/inspections/explore",
        json={"query": "cafe", "result_filter": "pass"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["restaurant_count"] == 1
    assert payload["restaurants"][0]["name"] == "SECOND CAFE"


def test_live_explorer_requires_complete_location_or_text() -> None:
    empty = client.post("/restaurants/inspections/explore", json={})
    incomplete = client.post(
        "/restaurants/inspections/explore", json={"latitude": 41.8781}
    )

    assert empty.status_code == 422
    assert incomplete.status_code == 422


def test_live_explorer_hides_provider_failures() -> None:
    app.dependency_overrides[get_inspection_provider] = FailingInspectionProvider
    try:
        response = client.post(
            "/restaurants/inspections/explore", json={"query": "cafe"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Live City inspection data is temporarily unavailable."
    }
