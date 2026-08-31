from bitecheck_api.restaurants.confidence import ReviewConfidenceRepository
from bitecheck_api.restaurants.insights import RecommendationInsightsRepository
from bitecheck_api.restaurants.models import (
    ConversationIntent,
    RecommendationCategory,
    RestaurantConversationRequest,
    RestaurantConversationResponse,
    RestaurantConversationState,
    RestaurantRankingRequest,
    RankingWeights,
)
from bitecheck_api.restaurants.parser import normalize_text
from bitecheck_api.restaurants.recommendations import RestaurantRecommendationService
from bitecheck_api.restaurants.repository import RestaurantRepository


SUPPORTED_EXAMPLES = (
    "Only show walkable options.",
    "Show me the cheapest one.",
    "Which has better vegetarian choices?",
    "Prioritize authenticity over distance.",
    "Which restaurant has the most reliable reviews?",
    "What are the common complaints?",
    "Show all options.",
    "Start over.",
)


class ConversationTransitionError(ValueError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.supported_examples = SUPPORTED_EXAMPLES


def transition_state(
    request: RestaurantConversationRequest,
) -> tuple[ConversationIntent, RestaurantConversationState, str]:
    text = normalize_text(request.message)
    state = request.state.model_copy(deep=True)

    if any(phrase in text for phrase in ("start over", "reset", "clear everything")):
        return (
            "reset",
            RestaurantConversationState(),
            "Cleared the current filters and conversational preferences.",
        )
    if any(phrase in text for phrase in ("show all", "all options", "show everything")):
        state.sort_mode = "weighted"
        state.travel_preference = "any"
        state.theme_preference = None
        state.result_limit = None
        return "show_all", state, "Showing all matches in weighted-score order."
    if "walkable" in text or "walking only" in text:
        if state.filters.starting_area is None:
            raise ConversationTransitionError(
                "A starting area is required before filtering to walkable options."
            )
        state.travel_preference = "walkable"
        state.result_limit = None
        return (
            "walkable_only",
            state,
            "Kept only results whose selected travel category uses walking.",
        )
    if "cheap" in text or "lowest cost" in text:
        state.sort_mode = "cheapest"
        state.result_limit = 1
        return "cheapest", state, "Sorted by estimated cost and kept the cheapest result."
    if "vegetarian" in text or "veggie" in text:
        state.filters.vegetarian_required = True
        state.sort_mode = "preferred_theme"
        state.theme_preference = "vegetarian_options"
        state.result_limit = 1
        return (
            "vegetarian_quality",
            state,
            "Required vegetarian availability, then prioritized positive vegetarian-option mentions.",
        )
    if "authentic" in text:
        state.sort_mode = "preferred_theme"
        state.theme_preference = "authenticity"
        return (
            "authenticity_priority",
            state,
            "Prioritized positive authenticity mentions, using weighted score to break ties.",
        )
    if "reliable" in text or "confidence" in text or "consistent reviews" in text:
        state.sort_mode = "review_confidence"
        state.result_limit = 1
        return (
            "review_reliability",
            state,
            "Sorted by Review Confidence and kept the strongest evidence result.",
        )
    if "complaint" in text or "concern" in text or "negative review" in text:
        state.result_limit = None
        return (
            "inspect_complaints",
            state,
            "Kept the current matches and exposed their leading negative review themes.",
        )
    raise ConversationTransitionError(
        "That follow-up is not supported by the current deterministic rules."
    )


class RestaurantConversationService:
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

    def follow_up(
        self, request: RestaurantConversationRequest
    ) -> RestaurantConversationResponse:
        intent, state, explanation = transition_state(request)
        recommendation_service = RestaurantRecommendationService(
            self._restaurant_repository,
            self._confidence_repository,
            self._insights_repository,
            self._default_weights,
        )
        results = recommendation_service.recommend(
            RestaurantRankingRequest(filters=state.filters)
        )
        cards = [card.model_copy(deep=True) for card in results.recommendations]

        if state.travel_preference == "walkable":
            cards = [
                card
                for card in cards
                if card.travel is not None and card.travel.selected_mode == "walking"
            ]

        insights = {
            item.restaurant_id: item
            for item in self._insights_repository.get_all().restaurants
        }
        if state.sort_mode == "cheapest":
            cards.sort(
                key=lambda card: (card.estimated_cost_per_person, -card.total_score)
            )
        elif state.sort_mode == "review_confidence":
            cards.sort(
                key=lambda card: (-card.review_confidence_score, -card.total_score)
            )
        elif state.sort_mode == "preferred_theme" and state.theme_preference:
            theme_preference = state.theme_preference
            cards.sort(
                key=lambda card: (
                    -insights[card.restaurant_id].positive_theme_counts.get(
                        theme_preference, 0
                    ),
                    -card.total_score,
                )
            )

        candidate_count = len(cards)
        if state.result_limit is not None:
            cards = cards[: state.result_limit]
        for rank, card in enumerate(cards, start=1):
            card.rank = rank
        assigned_set = {
            badge.category for card in cards for badge in card.categories
        }
        assigned_categories: list[RecommendationCategory] = [
            category
            for category in results.assigned_categories
            if category in assigned_set
        ]
        updated_results = results.model_copy(
            update={
                "match_count": len(cards),
                "recommendations": cards,
                "assigned_categories": assigned_categories,
            }
        )
        return RestaurantConversationResponse(
            intent=intent,
            state=state,
            transition_explanation=explanation,
            candidate_count_before_limit=candidate_count,
            results=updated_results,
        )
