from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from bitecheck_api.restaurants.models import RecommendationInsightsDataset


DEFAULT_RECOMMENDATION_INSIGHTS_PATH = (
    Path(__file__).resolve().parents[5]
    / "data"
    / "analytics"
    / "recommendation_insights.json"
)


class RecommendationInsightsDataError(RuntimeError):
    """Raised when card-ready review insights cannot be safely served."""


class RecommendationInsightsRepository(Protocol):
    def get_all(self) -> RecommendationInsightsDataset:
        """Return validated per-restaurant review insights."""


class JsonRecommendationInsightsRepository:
    def __init__(self, path: Path = DEFAULT_RECOMMENDATION_INSIGHTS_PATH) -> None:
        self._path = path

    def get_all(self) -> RecommendationInsightsDataset:
        try:
            raw_dataset = self._path.read_text(encoding="utf-8")
        except OSError as error:
            raise RecommendationInsightsDataError(
                "Recommendation insights are unavailable."
            ) from error
        try:
            dataset = RecommendationInsightsDataset.model_validate_json(raw_dataset)
        except ValidationError as error:
            raise RecommendationInsightsDataError(
                "Recommendation insights are invalid."
            ) from error

        if dataset.metadata.restaurant_count != len(dataset.restaurants):
            raise RecommendationInsightsDataError(
                "Recommendation insight metadata is inconsistent."
            )
        if len({item.restaurant_id for item in dataset.restaurants}) != len(
            dataset.restaurants
        ):
            raise RecommendationInsightsDataError(
                "Recommendation insight restaurant IDs are not unique."
            )
        return dataset


def get_recommendation_insights_repository() -> RecommendationInsightsRepository:
    return JsonRecommendationInsightsRepository()
