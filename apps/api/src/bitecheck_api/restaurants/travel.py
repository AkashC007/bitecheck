from collections import Counter

from bitecheck_api.restaurants.models import (
    RestaurantTravelCategoryItem,
    TransportationEstimate,
    TravelCategoryDecision,
    TravelCategoryRequest,
    TravelCategoryResponse,
    TravelCategoryThresholds,
    TravelConvenienceCategory,
    TravelMinutes,
    TravelMode,
)
from bitecheck_api.restaurants.repository import (
    RestaurantDataError,
    RestaurantRepository,
)
from bitecheck_api.restaurants.service import canonical_value


CATEGORY_LABELS: dict[TravelConvenienceCategory, str] = {
    "walkable": "Walkable",
    "comfortable_walk": "Comfortable walk",
    "easy_public_transit": "Easy public transit",
    "longer_public_transit": "Longer public transit",
    "easy_drive": "Easy drive",
    "inconvenient": "Inconvenient",
}

CATEGORY_ORDER: tuple[TravelConvenienceCategory, ...] = (
    "walkable",
    "comfortable_walk",
    "easy_public_transit",
    "longer_public_transit",
    "easy_drive",
    "inconvenient",
)


def _decision(
    category: TravelConvenienceCategory,
    mode: TravelMode,
    minutes: int,
) -> TravelCategoryDecision:
    return TravelCategoryDecision(
        category=category,
        selected_mode=mode,
        selected_minutes=minutes,
        explanation=f"{CATEGORY_LABELS[category]}: {minutes} minutes by "
        f"{mode.replace('_', ' ')}.",
    )


def categorize_travel(
    estimate: TransportationEstimate,
    thresholds: TravelCategoryThresholds,
) -> TravelCategoryDecision:
    """Assign one deterministic category, preferring walking before transit."""

    acceptable = thresholds.maximum_acceptable_minutes
    if (
        estimate.walking_minutes
        <= min(thresholds.walkable_max_minutes, acceptable)
    ):
        return _decision("walkable", "walking", estimate.walking_minutes)
    if (
        estimate.walking_minutes
        <= min(thresholds.comfortable_walk_max_minutes, acceptable)
    ):
        return _decision(
            "comfortable_walk",
            "walking",
            estimate.walking_minutes,
        )
    if (
        estimate.public_transit_minutes
        <= min(thresholds.easy_transit_max_minutes, acceptable)
    ):
        return _decision(
            "easy_public_transit",
            "public_transit",
            estimate.public_transit_minutes,
        )
    if (
        estimate.public_transit_minutes
        <= min(thresholds.longer_transit_max_minutes, acceptable)
    ):
        return _decision(
            "longer_public_transit",
            "public_transit",
            estimate.public_transit_minutes,
        )
    if (
        estimate.driving_minutes
        <= min(thresholds.easy_drive_max_minutes, acceptable)
    ):
        return _decision("easy_drive", "driving", estimate.driving_minutes)

    mode_minutes: tuple[tuple[TravelMode, int], ...] = (
        ("walking", estimate.walking_minutes),
        ("public_transit", estimate.public_transit_minutes),
        ("driving", estimate.driving_minutes),
    )
    fastest_mode, fastest_minutes = min(mode_minutes, key=lambda item: item[1])
    return TravelCategoryDecision(
        category="inconvenient",
        selected_mode=fastest_mode,
        selected_minutes=fastest_minutes,
        explanation=(
            "Inconvenient: no travel mode meets both its convenience threshold "
            f"and the {acceptable}-minute user limit; the fastest estimate is "
            f"{fastest_minutes} minutes by {fastest_mode.replace('_', ' ')}."
        ),
    )


class TransportationCategorizationService:
    def __init__(self, repository: RestaurantRepository) -> None:
        self._repository = repository

    def categorize(self, request: TravelCategoryRequest) -> TravelCategoryResponse:
        restaurants = self._repository.list_restaurants()
        starting_area = canonical_value(
            request.starting_area,
            (
                area
                for restaurant in restaurants
                for area in restaurant.estimated_transportation
            ),
            "starting_area",
        )
        if starting_area is None:
            raise RestaurantDataError("Starting area could not be resolved.")

        thresholds = request.thresholds()
        items: list[RestaurantTravelCategoryItem] = []
        counts: Counter[TravelConvenienceCategory] = Counter()

        for restaurant in restaurants:
            estimate = restaurant.estimated_transportation.get(starting_area)
            if estimate is None:
                raise RestaurantDataError(
                    "Restaurant transportation data is incomplete."
                )
            decision = categorize_travel(estimate, thresholds)
            counts[decision.category] += 1
            items.append(
                RestaurantTravelCategoryItem(
                    restaurant_id=restaurant.restaurant_id,
                    name=restaurant.name,
                    cuisine=restaurant.cuisine,
                    neighborhood=restaurant.neighborhood,
                    travel_minutes=TravelMinutes(
                        walking=estimate.walking_minutes,
                        public_transit=estimate.public_transit_minutes,
                        driving=estimate.driving_minutes,
                    ),
                    decision=decision,
                )
            )

        category_counts = {
            category: counts[category] for category in CATEGORY_ORDER
        }
        return TravelCategoryResponse(
            starting_area=starting_area,
            thresholds=thresholds,
            restaurant_count=len(items),
            category_counts=category_counts,
            restaurants=items,
        )
