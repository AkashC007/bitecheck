from collections.abc import Iterable

from bitecheck_api.restaurants.models import (
    RestaurantRecord,
    RestaurantSearchFilters,
    RestaurantSearchItem,
    RestaurantSearchResponse,
    TravelMatch,
)
from bitecheck_api.restaurants.repository import (
    RestaurantDataError,
    RestaurantRepository,
)


class InvalidFilterValue(ValueError):
    """Describe a filter value that is absent from the current dataset."""

    def __init__(
        self,
        field: str,
        value: str,
        allowed_values: tuple[str, ...],
    ) -> None:
        self.field = field
        self.value = value
        self.allowed_values = allowed_values
        super().__init__(f"Unsupported {field}: {value}")


def canonical_value(
    value: str | None,
    allowed_values: Iterable[str],
    field: str,
) -> str | None:
    if value is None:
        return None

    canonical_by_normalized = {
        allowed.casefold(): allowed for allowed in allowed_values
    }
    canonical = canonical_by_normalized.get(value.casefold())
    if canonical is None:
        raise InvalidFilterValue(
            field=field,
            value=value,
            allowed_values=tuple(sorted(canonical_by_normalized.values())),
        )
    return canonical


def _travel_match(
    restaurant: RestaurantRecord,
    starting_area: str,
) -> TravelMatch:
    estimate = restaurant.estimated_transportation.get(starting_area)
    if estimate is None:
        raise RestaurantDataError("Restaurant transportation data is incomplete.")

    if estimate.walking_minutes <= estimate.public_transit_minutes:
        return TravelMatch(
            starting_area=starting_area,
            mode="walking",
            minutes=estimate.walking_minutes,
        )

    return TravelMatch(
        starting_area=starting_area,
        mode="public_transit",
        minutes=estimate.public_transit_minutes,
    )


class RestaurantSearchService:
    def __init__(self, repository: RestaurantRepository) -> None:
        self._repository = repository

    def search(self, filters: RestaurantSearchFilters) -> RestaurantSearchResponse:
        restaurants = self._repository.list_restaurants()
        cuisine = canonical_value(
            filters.cuisine,
            (restaurant.cuisine for restaurant in restaurants),
            "cuisine",
        )
        starting_area = canonical_value(
            filters.starting_area,
            (
                area
                for restaurant in restaurants
                for area in restaurant.estimated_transportation
            ),
            "starting_area",
        )
        applied_filters = filters.model_copy(
            update={
                "cuisine": cuisine,
                "starting_area": starting_area,
            }
        )
        matches: list[RestaurantSearchItem] = []

        for restaurant in restaurants:
            if cuisine is not None and restaurant.cuisine != cuisine:
                continue
            if (
                filters.maximum_budget is not None
                and restaurant.estimated_cost_per_person > filters.maximum_budget
            ):
                continue
            if filters.vegetarian_required and not restaurant.vegetarian_available:
                continue

            travel = (
                _travel_match(restaurant, starting_area)
                if starting_area is not None
                else None
            )
            if (
                filters.maximum_travel_time is not None
                and travel is not None
                and travel.minutes > filters.maximum_travel_time
            ):
                continue

            matches.append(
                RestaurantSearchItem(
                    restaurant_id=restaurant.restaurant_id,
                    name=restaurant.name,
                    address=restaurant.address,
                    neighborhood=restaurant.neighborhood,
                    latitude=restaurant.latitude,
                    longitude=restaurant.longitude,
                    cuisine=restaurant.cuisine,
                    price_category=restaurant.price_category,
                    estimated_cost_per_person=(
                        restaurant.estimated_cost_per_person
                    ),
                    vegetarian_available=restaurant.vegetarian_available,
                    vegan_available=restaurant.vegan_available,
                    rating=restaurant.rating,
                    review_count=restaurant.review_count,
                    travel=travel,
                )
            )

        return RestaurantSearchResponse(
            applied_filters=applied_filters,
            match_count=len(matches),
            restaurants=matches,
        )
