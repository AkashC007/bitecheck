from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from bitecheck_api.restaurants.confidence import (
    ReviewConfidenceDataError,
    ReviewConfidenceRepository,
    get_review_confidence_repository,
)
from bitecheck_api.restaurants.conversation import (
    ConversationTransitionError,
    RestaurantConversationService,
)
from bitecheck_api.restaurants.models import (
    InspectionExplorerRequest,
    InspectionExplorerResponse,
    NaturalLanguageParseRequest,
    RestaurantConversationRequest,
    RestaurantConversationResponse,
    RestaurantRankingRequest,
    RestaurantRankingResponse,
    RestaurantRecommendationResponse,
    RestaurantSearchFilters,
    RestaurantSearchResponse,
    ReviewConfidenceDataset,
    TravelCategoryRequest,
    TravelCategoryResponse,
)
from bitecheck_api.restaurants.inspection_explorer import (
    InspectionExplorerService,
    InspectionProvider,
    InspectionProviderError,
    get_inspection_provider,
)
from bitecheck_api.restaurants.insights import (
    RecommendationInsightsDataError,
    RecommendationInsightsRepository,
    get_recommendation_insights_repository,
)
from bitecheck_api.restaurants.parser import (
    NaturalLanguageParseError,
    RestaurantRequestParser,
    get_restaurant_request_parser,
)
from bitecheck_api.restaurants.repository import (
    RestaurantDataError,
    RestaurantRepository,
    get_restaurant_repository,
)
from bitecheck_api.restaurants.ranking import (
    RankingConfigurationError,
    RestaurantRankingService,
    load_ranking_weights,
)
from bitecheck_api.restaurants.recommendations import (
    RestaurantRecommendationService,
)
from bitecheck_api.restaurants.service import (
    InvalidFilterValue,
    RestaurantSearchService,
)
from bitecheck_api.restaurants.travel import TransportationCategorizationService


router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.post(
    "/inspections/explore",
    response_model=InspectionExplorerResponse,
    summary="Explore live City of Chicago restaurant inspections",
)
async def explore_public_restaurant_inspections(
    request: InspectionExplorerRequest,
    provider: Annotated[
        InspectionProvider,
        Depends(get_inspection_provider),
    ],
) -> InspectionExplorerResponse:
    """Return deduplicated, source-backed inspection cards without demo fields."""

    try:
        return await InspectionExplorerService(provider).explore(request)
    except InspectionProviderError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Live City inspection data is temporarily unavailable.",
        ) from error


@router.post(
    "/conversation",
    response_model=RestaurantConversationResponse,
    summary="Apply a deterministic follow-up to restaurant conversation state",
)
def follow_up_restaurant_conversation(
    request: RestaurantConversationRequest,
    restaurant_repository: Annotated[
        RestaurantRepository,
        Depends(get_restaurant_repository),
    ],
    confidence_repository: Annotated[
        ReviewConfidenceRepository,
        Depends(get_review_confidence_repository),
    ],
    insights_repository: Annotated[
        RecommendationInsightsRepository,
        Depends(get_recommendation_insights_repository),
    ],
) -> RestaurantConversationResponse:
    """Update explicit state using free, inspectable follow-up rules."""

    try:
        weights = load_ranking_weights()
        return RestaurantConversationService(
            restaurant_repository,
            confidence_repository,
            insights_repository,
            weights,
        ).follow_up(request)
    except ConversationTransitionError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": str(error),
                "supported_examples": error.supported_examples,
            },
        ) from error
    except InvalidFilterValue as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "field": error.field,
                "message": str(error),
                "allowed_values": error.allowed_values,
            },
        ) from error
    except RestaurantDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Restaurant data is temporarily unavailable.",
        ) from error
    except (RankingConfigurationError, ReviewConfidenceDataError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation analytics are temporarily unavailable.",
        ) from error
    except RecommendationInsightsDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation insights are temporarily unavailable.",
        ) from error


@router.post(
    "/recommendations",
    response_model=RestaurantRecommendationResponse,
    summary="Build decision-focused restaurant recommendation cards",
)
def recommend_restaurants(
    request: RestaurantRankingRequest,
    restaurant_repository: Annotated[
        RestaurantRepository,
        Depends(get_restaurant_repository),
    ],
    confidence_repository: Annotated[
        ReviewConfidenceRepository,
        Depends(get_review_confidence_repository),
    ],
    insights_repository: Annotated[
        RecommendationInsightsRepository,
        Depends(get_recommendation_insights_repository),
    ],
) -> RestaurantRecommendationResponse:
    """Join ranking, travel, themes, confidence, and freshness for the UI."""

    try:
        weights = request.weights or load_ranking_weights()
        return RestaurantRecommendationService(
            restaurant_repository,
            confidence_repository,
            insights_repository,
            weights,
        ).recommend(request)
    except InvalidFilterValue as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "field": error.field,
                "message": str(error),
                "allowed_values": error.allowed_values,
            },
        ) from error
    except RestaurantDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Restaurant data is temporarily unavailable.",
        ) from error
    except RankingConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ranking configuration is temporarily unavailable.",
        ) from error
    except ReviewConfidenceDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Review-confidence analytics are temporarily unavailable.",
        ) from error
    except RecommendationInsightsDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation insights are temporarily unavailable.",
        ) from error


@router.post(
    "/rank",
    response_model=RestaurantRankingResponse,
    summary="Rank matching restaurants with explainable weighted scores",
)
def rank_restaurants(
    request: RestaurantRankingRequest,
    repository: Annotated[
        RestaurantRepository,
        Depends(get_restaurant_repository),
    ],
    review_confidence_repository: Annotated[
        ReviewConfidenceRepository,
        Depends(get_review_confidence_repository),
    ],
) -> RestaurantRankingResponse:
    """Filter, normalize, weight, and rank matching restaurants."""

    try:
        default_weights = request.weights or load_ranking_weights()
        return RestaurantRankingService(
            repository,
            review_confidence_repository,
            default_weights,
        ).rank(request)
    except InvalidFilterValue as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "field": error.field,
                "message": str(error),
                "allowed_values": error.allowed_values,
            },
        ) from error
    except RestaurantDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Restaurant data is temporarily unavailable.",
        ) from error
    except RankingConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ranking configuration is temporarily unavailable.",
        ) from error
    except ReviewConfidenceDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Review-confidence analytics are temporarily unavailable.",
        ) from error


@router.get(
    "/review-confidence",
    response_model=ReviewConfidenceDataset,
    summary="Inspect explainable review-confidence analytics",
)
def get_review_confidence(
    repository: Annotated[
        ReviewConfidenceRepository,
        Depends(get_review_confidence_repository),
    ],
) -> ReviewConfidenceDataset:
    """Return every component, contribution, penalty, and interpretation."""

    try:
        return repository.get_all()
    except ReviewConfidenceDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Review-confidence analytics are temporarily unavailable.",
        ) from error


@router.get(
    "/travel-categories",
    response_model=TravelCategoryResponse,
    summary="Categorize restaurants by travel convenience",
)
def categorize_restaurant_travel(
    request: Annotated[TravelCategoryRequest, Query()],
    repository: Annotated[
        RestaurantRepository,
        Depends(get_restaurant_repository),
    ],
) -> TravelCategoryResponse:
    """Classify synthetic travel estimates using configurable thresholds."""

    try:
        return TransportationCategorizationService(repository).categorize(request)
    except InvalidFilterValue as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "field": error.field,
                "message": str(error),
                "allowed_values": error.allowed_values,
            },
        ) from error
    except RestaurantDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Restaurant data is temporarily unavailable.",
        ) from error


@router.post(
    "/parse",
    response_model=RestaurantSearchFilters,
    summary="Parse a restaurant request into structured filters",
)
def parse_restaurant_request(
    request: NaturalLanguageParseRequest,
    parser: Annotated[
        RestaurantRequestParser,
        Depends(get_restaurant_request_parser),
    ],
) -> RestaurantSearchFilters:
    """Apply deterministic keyword and regular-expression parsing rules."""

    try:
        return parser.parse(request.text)
    except NaturalLanguageParseError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "field": error.field,
                "message": str(error),
                "candidates": error.candidates,
            },
        ) from error


@router.get(
    "/search",
    response_model=RestaurantSearchResponse,
    summary="Search hybrid Chicago restaurant records",
)
def search_restaurants(
    filters: Annotated[RestaurantSearchFilters, Query()],
    repository: Annotated[
        RestaurantRepository,
        Depends(get_restaurant_repository),
    ],
) -> RestaurantSearchResponse:
    """Apply structured filters without ranking the matching restaurants."""

    try:
        return RestaurantSearchService(repository).search(filters)
    except InvalidFilterValue as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "field": error.field,
                "message": str(error),
                "allowed_values": error.allowed_values,
            },
        ) from error
    except RestaurantDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Restaurant data is temporarily unavailable.",
        ) from error
