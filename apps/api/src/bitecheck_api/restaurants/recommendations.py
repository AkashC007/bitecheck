from statistics import median

from bitecheck_api.restaurants.confidence import (
    ReviewConfidenceDataError,
    ReviewConfidenceRepository,
    confidence_scores,
)
from bitecheck_api.restaurants.insights import (
    RecommendationInsightsDataError,
    RecommendationInsightsRepository,
)
from bitecheck_api.restaurants.models import (
    RecommendationBadge,
    RecommendationCategory,
    RecommendationTravel,
    RestaurantRecommendationCard,
    RestaurantRecommendationResponse,
    RestaurantReviewConfidence,
    RestaurantRankingRequest,
    RankingWeights,
    TravelCategoryThresholds,
)
from bitecheck_api.restaurants.ranking import RestaurantRankingService
from bitecheck_api.restaurants.repository import RestaurantRepository
from bitecheck_api.restaurants.travel import categorize_travel


CATEGORY_ORDER: tuple[RecommendationCategory, ...] = (
    "best_overall",
    "best_walkable",
    "best_public_transportation",
    "best_value",
    "most_consistently_recommended",
    "best_vegetarian_match",
    "hidden_gem",
    "mixed_reviews",
)

CATEGORY_LABELS: dict[RecommendationCategory, str] = {
    "best_overall": "Best overall",
    "best_walkable": "Best walkable",
    "best_public_transportation": "Best by public transportation",
    "best_value": "Best value",
    "most_consistently_recommended": "Most consistently recommended",
    "best_vegetarian_match": "Best vegetarian match",
    "hidden_gem": "Hidden gem",
    "mixed_reviews": "Mixed reviews — proceed carefully",
}


class RestaurantRecommendationService:
    def __init__(
        self,
        restaurant_repository: RestaurantRepository,
        confidence_repository: ReviewConfidenceRepository,
        insights_repository: RecommendationInsightsRepository,
        default_weights: RankingWeights,
    ) -> None:
        self._restaurant_repository = restaurant_repository
        self._confidence_repository = confidence_repository
        self._insights_repository = insights_repository
        self._default_weights = default_weights

    def recommend(
        self, request: RestaurantRankingRequest
    ) -> RestaurantRecommendationResponse:
        ranking = RestaurantRankingService(
            self._restaurant_repository,
            self._confidence_repository,
            self._default_weights,
        ).rank(request)
        records = {
            item.restaurant_id: item
            for item in self._restaurant_repository.list_restaurants()
        }
        confidence = confidence_scores(self._confidence_repository)
        insights = {
            item.restaurant_id: item
            for item in self._insights_repository.get_all().restaurants
        }
        ranked_ids = {item.restaurant_id for item in ranking.rankings}
        if not ranked_ids.issubset(confidence):
            raise ReviewConfidenceDataError(
                "Review confidence does not cover every ranked restaurant."
            )
        if not ranked_ids.issubset(insights):
            raise RecommendationInsightsDataError(
                "Recommendation insights do not cover every ranked restaurant."
            )

        cards: list[RestaurantRecommendationCard] = []
        for ranked in ranking.rankings:
            record = records[ranked.restaurant_id]
            confidence_item = confidence[ranked.restaurant_id]
            insight = insights[ranked.restaurant_id]
            travel: RecommendationTravel | None = None
            if ranking.filters.starting_area is not None:
                estimate = record.estimated_transportation[
                    ranking.filters.starting_area
                ]
                thresholds = TravelCategoryThresholds(
                    maximum_acceptable_minutes=(
                        ranking.filters.maximum_travel_time or 50
                    )
                )
                decision = categorize_travel(estimate, thresholds)
                travel = RecommendationTravel(
                    starting_area=ranking.filters.starting_area,
                    walking_minutes=estimate.walking_minutes,
                    public_transit_minutes=estimate.public_transit_minutes,
                    driving_minutes=estimate.driving_minutes,
                    category=decision.category,
                    selected_mode=decision.selected_mode,
                    selected_minutes=decision.selected_minutes,
                    explanation=decision.explanation,
                )

            cards.append(
                RestaurantRecommendationCard(
                    rank=ranked.rank,
                    restaurant_id=ranked.restaurant_id,
                    name=record.name,
                    address=record.address,
                    latitude=record.latitude,
                    longitude=record.longitude,
                    cuisine=record.cuisine,
                    neighborhood=record.neighborhood,
                    price_category=record.price_category,
                    estimated_cost_per_person=record.estimated_cost_per_person,
                    vegetarian_available=record.vegetarian_available,
                    vegan_available=record.vegan_available,
                    rating=record.rating,
                    dataset_review_count=record.review_count,
                    total_score=ranked.total_score,
                    categories=[],
                    travel=travel,
                    top_positive_themes=insight.top_positive_themes,
                    top_negative_themes=insight.top_negative_themes,
                    review_confidence_score=(
                        confidence_item.review_confidence_score
                    ),
                    review_confidence_band=confidence_item.confidence_band,
                    ranking_factors=ranked.factors,
                    ranking_explanation=ranked.summary,
                    latest_review_date=insight.latest_review_date,
                    data_freshness_label=(
                        f"Latest synthetic review: {insight.latest_review_date}"
                    ),
                    latest_inspection=record.latest_inspection,
                )
            )

        assigned = self._assign_categories(
            cards,
            confidence,
            ranking.filters.maximum_travel_time or 50,
        )
        return RestaurantRecommendationResponse(
            filters=ranking.filters,
            configured_weights=ranking.configured_weights,
            match_count=len(cards),
            assigned_categories=assigned,
            recommendations=cards,
            data_notice=(
                "Restaurant identities, addresses, coordinates, and inspection "
                "records come from a fixed City of Chicago snapshot dated "
                "2026-08-30. Cuisines, prices, dietary flags, ratings, reviews, "
                "themes, confidence, hours, and travel times are synthetic demo data."
            ),
        )

    @staticmethod
    def _assign_categories(
        cards: list[RestaurantRecommendationCard],
        confidence: dict[str, RestaurantReviewConfidence],
        maximum_acceptable_minutes: int,
    ) -> list[RecommendationCategory]:
        if not cards:
            return []

        assignments: dict[RecommendationCategory, tuple[str, str]] = {}
        assignments["best_overall"] = (
            cards[0].restaurant_id,
            f"Highest weighted recommendation score at {cards[0].total_score:.2f}/100.",
        )

        walkable = [
            card
            for card in cards
            if card.travel is not None and card.travel.selected_mode == "walking"
        ]
        if walkable:
            winner = walkable[0]
            winner_travel = winner.travel
            if winner_travel is None:
                raise AssertionError("walkable candidates must include travel data")
            assignments["best_walkable"] = (
                winner.restaurant_id,
                f"Highest-ranked walking option at {winner_travel.selected_minutes} minutes.",
            )

        transit = [
            card
            for card in cards
            if card.travel is not None
            and card.travel.public_transit_minutes
            <= maximum_acceptable_minutes
        ]
        if transit:
            winner = transit[0]
            winner_travel = winner.travel
            if winner_travel is None:
                raise AssertionError("transit candidates must include travel data")
            assignments["best_public_transportation"] = (
                winner.restaurant_id,
                f"Highest-ranked transit option at {winner_travel.public_transit_minutes} minutes.",
            )

        value = min(
            cards,
            key=lambda card: (card.estimated_cost_per_person, -card.total_score),
        )
        assignments["best_value"] = (
            value.restaurant_id,
            f"Lowest estimated cost among these matches at ${value.estimated_cost_per_person} per person.",
        )

        consistent = max(
            cards,
            key=lambda card: (card.review_confidence_score, card.total_score),
        )
        assignments["most_consistently_recommended"] = (
            consistent.restaurant_id,
            f"Highest Review Confidence in this result set at {consistent.review_confidence_score:.2f}/100.",
        )

        vegetarian = [card for card in cards if card.vegetarian_available]
        if vegetarian:
            winner = vegetarian[0]
            assignments["best_vegetarian_match"] = (
                winner.restaurant_id,
                "Highest-ranked result with synthetic vegetarian availability.",
            )

        review_count_median = median(card.dataset_review_count for card in cards)
        hidden_gems = [
            card
            for card in cards
            if card.dataset_review_count <= review_count_median
            and card.rating >= 4
            and card.review_confidence_score >= 65
        ]
        if hidden_gems:
            winner = hidden_gems[0]
            assignments["hidden_gem"] = (
                winner.restaurant_id,
                f"Strong score with {winner.dataset_review_count} dataset ratings, below this result set's median.",
            )

        mixed = min(
            cards,
            key=lambda card: (
                confidence[card.restaurant_id]
                .components["rating_consistency"]
                .score,
                -sum(theme.mention_count for theme in card.top_negative_themes),
            ),
        )
        consistency_score = confidence[mixed.restaurant_id].components[
            "rating_consistency"
        ].score
        if consistency_score < 60:
            assignments["mixed_reviews"] = (
                mixed.restaurant_id,
                f"Rating-consistency component is {consistency_score:.2f}/100; inspect the mixed themes.",
            )

        cards_by_id = {card.restaurant_id: card for card in cards}
        for category in CATEGORY_ORDER:
            assignment = assignments.get(category)
            if assignment is None:
                continue
            restaurant_id, reason = assignment
            cards_by_id[restaurant_id].categories.append(
                RecommendationBadge(
                    category=category,
                    label=CATEGORY_LABELS[category],
                    reason=reason,
                )
            )
        return [category for category in CATEGORY_ORDER if category in assignments]
