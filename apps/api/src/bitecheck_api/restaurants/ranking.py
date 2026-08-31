from pathlib import Path

from pydantic import ValidationError

from bitecheck_api.restaurants.confidence import (
    ReviewConfidenceRepository,
    confidence_scores,
)
from bitecheck_api.restaurants.models import (
    RankedRestaurant,
    RankingConfiguration,
    RankingFactor,
    RankingFactorScore,
    RankingFactorStatus,
    RankingWeights,
    RestaurantRankingRequest,
    RestaurantRankingResponse,
    RestaurantReviewConfidence,
    RestaurantSearchItem,
)
from bitecheck_api.restaurants.repository import RestaurantRepository
from bitecheck_api.restaurants.service import RestaurantSearchService


DEFAULT_RANKING_CONFIG_PATH = (
    Path(__file__).resolve().parents[5] / "config" / "ranking_weights.json"
)
FACTOR_ORDER: tuple[RankingFactor, ...] = (
    "cuisine_match",
    "dietary_match",
    "budget_match",
    "travel_convenience",
    "rating",
    "review_confidence",
)


class RankingConfigurationError(RuntimeError):
    """Raised when ranking configuration is missing or invalid."""


def load_ranking_weights(
    path: Path = DEFAULT_RANKING_CONFIG_PATH,
) -> RankingWeights:
    try:
        raw_config = path.read_text(encoding="utf-8")
    except OSError as error:
        raise RankingConfigurationError("Ranking configuration is unavailable.") from error
    try:
        return RankingConfiguration.model_validate_json(raw_config).weights
    except ValidationError as error:
        raise RankingConfigurationError("Ranking configuration is invalid.") from error


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _raw_scores(
    item: RestaurantSearchItem,
    request: RestaurantRankingRequest,
    review_confidence: RestaurantReviewConfidence | None,
) -> dict[RankingFactor, tuple[float | None, RankingFactorStatus, str]]:
    filters = request.filters
    budget_score = (
        _clamp_score(
            100 * (1 - item.estimated_cost_per_person / (2 * filters.maximum_budget))
        )
        if filters.maximum_budget is not None
        else None
    )
    travel_limit = filters.maximum_travel_time or 50
    travel_score = (
        _clamp_score(100 * (1 - item.travel.minutes / (2 * travel_limit)))
        if item.travel is not None
        else None
    )
    return {
        "cuisine_match": (
            100.0 if filters.cuisine is not None else None,
            "active" if filters.cuisine is not None else "not_applicable",
            "Matches the requested cuisine."
            if filters.cuisine is not None
            else "No cuisine preference was supplied.",
        ),
        "dietary_match": (
            100.0 if filters.vegetarian_required else None,
            "active" if filters.vegetarian_required else "not_applicable",
            "Provides the required vegetarian option."
            if filters.vegetarian_required
            else "No dietary requirement was supplied.",
        ),
        "budget_match": (
            budget_score,
            "active" if budget_score is not None else "not_applicable",
            f"Estimated cost is ${item.estimated_cost_per_person} against the "
            f"${filters.maximum_budget} limit."
            if filters.maximum_budget is not None
            else "No maximum budget was supplied.",
        ),
        "travel_convenience": (
            travel_score,
            "active" if travel_score is not None else "not_applicable",
            f"Fastest non-driving estimate is {item.travel.minutes} minutes."
            if item.travel is not None
            else "No starting area was supplied.",
        ),
        "rating": (
            _clamp_score((item.rating - 1) / 4 * 100),
            "active",
            f"Dataset rating is {item.rating:.1f} out of 5.",
        ),
        "review_confidence": (
            review_confidence.review_confidence_score
            if review_confidence is not None
            else None,
            "active" if review_confidence is not None else "unavailable",
            (
                f"Review evidence confidence is "
                f"{review_confidence.review_confidence_score:.2f}/100 "
                f"({review_confidence.confidence_band}); this estimates evidence "
                "reliability, not truth."
                if review_confidence is not None
                else "Review-confidence analytics are unavailable for this restaurant."
            ),
        ),
    }


class RestaurantRankingService:
    def __init__(
        self,
        repository: RestaurantRepository,
        review_confidence_repository: ReviewConfidenceRepository,
        default_weights: RankingWeights,
    ) -> None:
        self._repository = repository
        self._review_confidence_repository = review_confidence_repository
        self._default_weights = default_weights

    def rank(self, request: RestaurantRankingRequest) -> RestaurantRankingResponse:
        weights = request.weights or self._default_weights
        search_response = RestaurantSearchService(self._repository).search(
            request.filters
        )
        confidence_by_restaurant = confidence_scores(
            self._review_confidence_repository
        )
        scored: list[RankedRestaurant] = []

        for item in search_response.restaurants:
            raw = _raw_scores(
                item,
                request,
                confidence_by_restaurant.get(item.restaurant_id),
            )
            active_weight = sum(
                getattr(weights, factor)
                for factor in FACTOR_ORDER
                if raw[factor][1] == "active"
            )
            factors: dict[RankingFactor, RankingFactorScore] = {}
            for factor in FACTOR_ORDER:
                score, factor_status, explanation = raw[factor]
                configured_weight = getattr(weights, factor)
                effective_weight = (
                    configured_weight / active_weight
                    if factor_status == "active" and active_weight > 0
                    else 0.0
                )
                contribution = (score or 0.0) * effective_weight
                factors[factor] = RankingFactorScore(
                    status=factor_status,
                    score=round(score, 2) if score is not None else None,
                    configured_weight=configured_weight,
                    effective_weight=round(effective_weight, 6),
                    contribution=round(contribution, 2),
                    explanation=explanation,
                )

            total = round(sum(detail.contribution for detail in factors.values()), 2)
            strongest = max(
                (
                    (factor, detail.contribution)
                    for factor, detail in factors.items()
                    if detail.status == "active"
                ),
                key=lambda pair: pair[1],
            )[0]
            scored.append(
                RankedRestaurant(
                    rank=1,
                    restaurant_id=item.restaurant_id,
                    name=item.name,
                    cuisine=item.cuisine,
                    neighborhood=item.neighborhood,
                    estimated_cost_per_person=item.estimated_cost_per_person,
                    rating=item.rating,
                    total_score=total,
                    factors=factors,
                    summary=f"Strongest score contribution: {strongest.replace('_', ' ')}.",
                )
            )

        scored.sort(key=lambda item: -item.total_score)
        previous_score: float | None = None
        current_rank = 0
        for position, ranked_item in enumerate(scored, start=1):
            if ranked_item.total_score != previous_score:
                current_rank = position
                previous_score = ranked_item.total_score
            ranked_item.rank = current_rank

        unavailable_factors: list[RankingFactor] = []
        if any(
            ranked.factors["review_confidence"].status == "unavailable"
            for ranked in scored
        ):
            unavailable_factors.append("review_confidence")

        return RestaurantRankingResponse(
            filters=search_response.applied_filters,
            configured_weights=weights,
            match_count=len(scored),
            unavailable_factors=unavailable_factors,
            rankings=scored,
        )
