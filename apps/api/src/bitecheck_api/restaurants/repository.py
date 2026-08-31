import os
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from bitecheck_api.restaurants.models import RestaurantDataset, RestaurantRecord


DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parents[5]
    / "data"
    / "synthetic"
    / "restaurants.json"
)


class RestaurantDataError(RuntimeError):
    """Raised when the configured restaurant source cannot be trusted."""


class RestaurantRepository(Protocol):
    def list_restaurants(self) -> tuple[RestaurantRecord, ...]:
        """Return validated restaurant records in stable source order."""


class JsonRestaurantRepository:
    """Load and validate restaurant records from the synthetic JSON adapter."""

    def __init__(self, dataset_path: Path) -> None:
        self._dataset_path = dataset_path

    def list_restaurants(self) -> tuple[RestaurantRecord, ...]:
        try:
            raw_dataset = self._dataset_path.read_text(encoding="utf-8")
        except OSError as error:
            raise RestaurantDataError("Restaurant data is unavailable.") from error

        try:
            dataset = RestaurantDataset.model_validate_json(raw_dataset)
        except ValidationError as error:
            raise RestaurantDataError("Restaurant data is invalid.") from error

        if dataset.metadata.record_count != len(dataset.restaurants):
            raise RestaurantDataError("Restaurant record count is inconsistent.")

        return tuple(dataset.restaurants)


def get_restaurant_repository() -> RestaurantRepository:
    configured_path = os.getenv("RESTAURANT_DATA_PATH")
    dataset_path = (
        Path(configured_path).expanduser()
        if configured_path is not None
        else DEFAULT_DATASET_PATH
    )
    return JsonRestaurantRepository(dataset_path)
