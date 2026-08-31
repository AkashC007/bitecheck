from pathlib import Path

from fastapi.testclient import TestClient

from bitecheck_api.main import app
from bitecheck_api.restaurants.confidence import (
    JsonReviewConfidenceRepository,
    ReviewConfidenceDataError,
    get_review_confidence_repository,
)


client = TestClient(app)


def test_review_confidence_endpoint_displays_every_component() -> None:
    response = client.get("/restaurants/review-confidence")

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["restaurant_count"] == 24
    assert payload["metadata"]["not_a_truth_score"] is True
    assert len(payload["restaurants"]) == 24
    first = payload["restaurants"][0]
    assert len(first["components"]) == 7
    assert len(first["penalties"]) == 4
    assert 0 <= first["review_confidence_score"] <= 100
    assert first["review_confidence_score"] == (
        first["base_score"] - first["total_penalty"]
    )


def test_repository_rejects_missing_invalid_and_inconsistent_data(
    tmp_path: Path,
) -> None:
    missing = JsonReviewConfidenceRepository(tmp_path / "missing.json")
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{}", encoding="utf-8")
    invalid = JsonReviewConfidenceRepository(invalid_path)

    for repository in (missing, invalid):
        try:
            repository.get_all()
        except ReviewConfidenceDataError:
            pass
        else:
            raise AssertionError("invalid analytics should be rejected")


def test_review_confidence_endpoint_returns_safe_503() -> None:
    class MissingRepository:
        def get_all(self) -> object:
            raise ReviewConfidenceDataError("private diagnostic")

    app.dependency_overrides[get_review_confidence_repository] = MissingRepository
    try:
        response = client.get("/restaurants/review-confidence")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Review-confidence analytics are temporarily unavailable."
    }
