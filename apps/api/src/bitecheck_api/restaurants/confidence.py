from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from bitecheck_api.restaurants.models import (
    RestaurantReviewConfidence,
    ReviewConfidenceDataset,
)


DEFAULT_REVIEW_CONFIDENCE_PATH = (
    Path(__file__).resolve().parents[5]
    / "data"
    / "analytics"
    / "review_confidence.json"
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


class ReviewConfidenceDataError(RuntimeError):
    """Raised when review-confidence analytics cannot be safely served."""


class ReviewConfidenceRepository(Protocol):
    def get_all(self) -> ReviewConfidenceDataset:
        """Return the validated review-confidence analytics artifact."""


class JsonReviewConfidenceRepository:
    def __init__(self, path: Path = DEFAULT_REVIEW_CONFIDENCE_PATH) -> None:
        self._path = path

    def get_all(self) -> ReviewConfidenceDataset:
        try:
            raw_dataset = self._path.read_text(encoding="utf-8")
        except OSError as error:
            raise ReviewConfidenceDataError(
                "Review-confidence analytics are unavailable."
            ) from error

        try:
            dataset = ReviewConfidenceDataset.model_validate_json(raw_dataset)
        except ValidationError as error:
            raise ReviewConfidenceDataError(
                "Review-confidence analytics are invalid."
            ) from error

        if dataset.metadata.restaurant_count != len(dataset.restaurants):
            raise ReviewConfidenceDataError(
                "Review-confidence metadata does not match the records."
            )
        if len({item.restaurant_id for item in dataset.restaurants}) != len(
            dataset.restaurants
        ):
            raise ReviewConfidenceDataError(
                "Review-confidence restaurant IDs are not unique."
            )
        if set(dataset.configuration.component_weights) != EXPECTED_COMPONENTS:
            raise ReviewConfidenceDataError(
                "Review-confidence component configuration is incomplete."
            )
        if set(dataset.configuration.maximum_penalties) != EXPECTED_PENALTIES:
            raise ReviewConfidenceDataError(
                "Review-confidence penalty configuration is incomplete."
            )
        for item in dataset.restaurants:
            if set(item.components) != EXPECTED_COMPONENTS:
                raise ReviewConfidenceDataError(
                    "A restaurant has incomplete confidence components."
                )
            if set(item.penalties) != EXPECTED_PENALTIES:
                raise ReviewConfidenceDataError(
                    "A restaurant has incomplete confidence penalties."
                )
        return dataset


def confidence_scores(
    repository: ReviewConfidenceRepository,
) -> dict[str, RestaurantReviewConfidence]:
    return {
        item.restaurant_id: item for item in repository.get_all().restaurants
    }


def get_review_confidence_repository() -> ReviewConfidenceRepository:
    return JsonReviewConfidenceRepository()
