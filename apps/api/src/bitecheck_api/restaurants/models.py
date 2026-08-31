from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    """Base model that rejects unexpected fields."""

    model_config = ConfigDict(extra="forbid")


class OpeningPeriod(StrictModel):
    open: str
    close: str


class TransportationEstimate(StrictModel):
    straight_line_distance_km: float = Field(ge=0)
    walking_minutes: int = Field(gt=0)
    public_transit_minutes: int = Field(gt=0)
    driving_minutes: int = Field(gt=0)
    estimate_type: Literal["synthetic"]


class LatestInspection(StrictModel):
    inspection_id: str
    inspection_date: str
    result: Literal["Pass", "Pass w/ Conditions"]
    inspection_type: str
    risk: str


class InspectionHistory(StrictModel):
    start_date: str
    end_date: str
    inspection_count: int = Field(gt=0)
    pass_count: int = Field(ge=0)
    pass_with_conditions_count: int = Field(ge=0)
    fail_count: int = Field(ge=0)


class RestaurantRecord(StrictModel):
    restaurant_id: str
    license_number: str
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    neighborhood: str
    latitude: float
    longitude: float
    cuisine: str
    price_category: Literal["$", "$$", "$$$"]
    estimated_cost_per_person: int = Field(gt=0)
    vegetarian_available: bool
    vegan_available: bool
    rating: float = Field(ge=1, le=5)
    review_count: int = Field(ge=0)
    opening_hours: dict[str, OpeningPeriod | None]
    estimated_transportation: dict[str, TransportationEstimate]
    latest_inspection: LatestInspection
    inspection_history: InspectionHistory
    identity_provenance: Literal["city_of_chicago_food_inspections"]
    profile_provenance: Literal["synthetic_enrichment"]
    data_provenance: Literal["hybrid"]


class DatasetMetadata(StrictModel):
    dataset_name: str
    description: str
    city: str
    hybrid: Literal[True]
    synthetic: Literal[False]
    seed: int
    record_count: int = Field(gt=0)
    generator_version: str
    schema_version: str
    identity_source: str
    identity_source_url: str
    identity_snapshot_date: str
    synthetic_fields: list[str]
    source_disclaimer: str


class RestaurantDataset(StrictModel):
    metadata: DatasetMetadata
    restaurants: list[RestaurantRecord]


class RestaurantSearchFilters(StrictModel):
    cuisine: str | None = Field(default=None, min_length=1)
    maximum_budget: int | None = Field(default=None, gt=0)
    vegetarian_required: bool = False
    starting_area: str | None = Field(default=None, min_length=1)
    maximum_travel_time: int | None = Field(default=None, gt=0)

    @field_validator("cuisine", "starting_area", mode="before")
    @classmethod
    def strip_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def require_starting_area_for_travel_limit(self) -> Self:
        if self.maximum_travel_time is not None and self.starting_area is None:
            raise ValueError(
                "starting_area is required when maximum_travel_time is provided"
            )
        return self


class NaturalLanguageParseRequest(StrictModel):
    text: str = Field(min_length=1, max_length=500)

    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class TravelMatch(StrictModel):
    starting_area: str
    mode: Literal["walking", "public_transit"]
    minutes: int = Field(gt=0)


class RestaurantSearchItem(StrictModel):
    restaurant_id: str
    name: str
    address: str
    neighborhood: str
    latitude: float
    longitude: float
    cuisine: str
    price_category: Literal["$", "$$", "$$$"]
    estimated_cost_per_person: int
    vegetarian_available: bool
    vegan_available: bool
    rating: float
    review_count: int
    latest_inspection: LatestInspection
    travel: TravelMatch | None = None


class RestaurantSearchResponse(StrictModel):
    applied_filters: RestaurantSearchFilters
    match_count: int = Field(ge=0)
    restaurants: list[RestaurantSearchItem]


TravelConvenienceCategory = Literal[
    "walkable",
    "comfortable_walk",
    "easy_public_transit",
    "longer_public_transit",
    "easy_drive",
    "inconvenient",
]
TravelMode = Literal["walking", "public_transit", "driving"]


class TravelCategoryThresholds(StrictModel):
    walkable_max_minutes: int = Field(default=15, gt=0)
    comfortable_walk_max_minutes: int = Field(default=25, gt=0)
    easy_transit_max_minutes: int = Field(default=30, gt=0)
    longer_transit_max_minutes: int = Field(default=50, gt=0)
    easy_drive_max_minutes: int = Field(default=20, gt=0)
    maximum_acceptable_minutes: int = Field(default=50, gt=0)

    @model_validator(mode="after")
    def validate_threshold_order(self) -> Self:
        if self.comfortable_walk_max_minutes < self.walkable_max_minutes:
            raise ValueError(
                "comfortable_walk_max_minutes must be greater than or equal to "
                "walkable_max_minutes"
            )
        if self.longer_transit_max_minutes < self.easy_transit_max_minutes:
            raise ValueError(
                "longer_transit_max_minutes must be greater than or equal to "
                "easy_transit_max_minutes"
            )
        return self


class TravelCategoryRequest(TravelCategoryThresholds):
    starting_area: str = Field(min_length=1)

    @field_validator("starting_area", mode="before")
    @classmethod
    def strip_starting_area(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    def thresholds(self) -> TravelCategoryThresholds:
        return TravelCategoryThresholds.model_validate(
            self.model_dump(exclude={"starting_area"})
        )


class TravelMinutes(StrictModel):
    walking: int = Field(gt=0)
    public_transit: int = Field(gt=0)
    driving: int = Field(gt=0)


class TravelCategoryDecision(StrictModel):
    category: TravelConvenienceCategory
    selected_mode: TravelMode
    selected_minutes: int = Field(gt=0)
    explanation: str


class RestaurantTravelCategoryItem(StrictModel):
    restaurant_id: str
    name: str
    cuisine: str
    neighborhood: str
    travel_minutes: TravelMinutes
    decision: TravelCategoryDecision


class TravelCategoryResponse(StrictModel):
    starting_area: str
    thresholds: TravelCategoryThresholds
    restaurant_count: int = Field(ge=0)
    category_counts: dict[TravelConvenienceCategory, int]
    restaurants: list[RestaurantTravelCategoryItem]


RankingFactor = Literal[
    "cuisine_match",
    "dietary_match",
    "budget_match",
    "travel_convenience",
    "rating",
    "review_confidence",
]
RankingFactorStatus = Literal["active", "not_applicable", "unavailable"]


class RankingWeights(StrictModel):
    cuisine_match: float = Field(ge=0, le=1)
    dietary_match: float = Field(ge=0, le=1)
    budget_match: float = Field(ge=0, le=1)
    travel_convenience: float = Field(ge=0, le=1)
    rating: float = Field(gt=0, le=1)
    review_confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def require_weights_to_sum_to_one(self) -> Self:
        if abs(sum(self.model_dump().values()) - 1.0) > 1e-9:
            raise ValueError("ranking weights must sum to 1.0")
        return self


class RankingConfiguration(StrictModel):
    schema_version: str
    weights: RankingWeights


class RestaurantRankingRequest(StrictModel):
    filters: RestaurantSearchFilters = Field(default_factory=RestaurantSearchFilters)
    weights: RankingWeights | None = None


class RankingFactorScore(StrictModel):
    status: RankingFactorStatus
    score: float | None = Field(default=None, ge=0, le=100)
    configured_weight: float = Field(ge=0, le=1)
    effective_weight: float = Field(ge=0, le=1)
    contribution: float = Field(ge=0, le=100)
    explanation: str


class RankedRestaurant(StrictModel):
    rank: int = Field(gt=0)
    restaurant_id: str
    name: str
    cuisine: str
    neighborhood: str
    estimated_cost_per_person: int = Field(gt=0)
    rating: float = Field(ge=1, le=5)
    total_score: float = Field(ge=0, le=100)
    factors: dict[RankingFactor, RankingFactorScore]
    summary: str


class RestaurantRankingResponse(StrictModel):
    filters: RestaurantSearchFilters
    configured_weights: RankingWeights
    match_count: int = Field(ge=0)
    unavailable_factors: list[RankingFactor]
    rankings: list[RankedRestaurant]


ReviewConfidenceComponentName = Literal[
    "cross_source_agreement",
    "observation_volume",
    "review_recency",
    "source_diversity",
    "review_specificity",
    "branch_match_confidence",
    "rating_consistency",
]
ReviewConfidencePenaltyName = Literal[
    "exact_duplicates",
    "repetitive_language",
    "suspicious_bursts",
    "missing_data",
]


class ReviewConfidenceComponent(StrictModel):
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    contribution: float = Field(ge=0, le=100)
    explanation: str


class ReviewConfidencePenalty(StrictModel):
    rate: float = Field(ge=0, le=1)
    maximum_penalty: float = Field(ge=0, le=100)
    penalty: float = Field(ge=0, le=100)
    explanation: str


class ReviewConfidenceSourceMetric(StrictModel):
    source: str
    review_count: int = Field(ge=0)
    mean_rating: float = Field(ge=1, le=5)


class RestaurantReviewConfidence(StrictModel):
    restaurant_id: str
    restaurant_name: str
    observation_count: int = Field(ge=0)
    source_metrics: list[ReviewConfidenceSourceMetric]
    components: dict[ReviewConfidenceComponentName, ReviewConfidenceComponent]
    base_score: float = Field(ge=0, le=100)
    penalties: dict[ReviewConfidencePenaltyName, ReviewConfidencePenalty]
    total_penalty: float = Field(ge=0, le=100)
    review_confidence_score: float = Field(ge=0, le=100)
    confidence_band: Literal["low", "medium", "high"]
    interpretation: str


class ReviewConfidenceMetadata(StrictModel):
    dataset_name: str
    scorer_version: str
    reference_date: str
    restaurant_count: int = Field(ge=0)
    review_count: int = Field(ge=0)
    not_a_truth_score: Literal[True]


class ReviewConfidenceTargets(StrictModel):
    observation_count: int = Field(gt=0)
    source_count: int = Field(gt=0)
    freshness_days: int = Field(gt=0)
    specificity_theme_count: int = Field(gt=0)


class ReviewConfidenceBands(StrictModel):
    high_minimum: float = Field(ge=0, le=100)
    medium_minimum: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def require_ordered_bands(self) -> Self:
        if self.high_minimum < self.medium_minimum:
            raise ValueError("high_minimum must be at least medium_minimum")
        return self


class ReviewConfidenceConfiguration(StrictModel):
    schema_version: str
    component_weights: dict[ReviewConfidenceComponentName, float]
    targets: ReviewConfidenceTargets
    maximum_penalties: dict[ReviewConfidencePenaltyName, float]
    bands: ReviewConfidenceBands

    @model_validator(mode="after")
    def require_component_weights_to_sum_to_one(self) -> Self:
        if abs(sum(self.component_weights.values()) - 1.0) > 1e-9:
            raise ValueError("review-confidence component weights must sum to 1.0")
        return self


class ReviewConfidenceDataset(StrictModel):
    metadata: ReviewConfidenceMetadata
    configuration: ReviewConfidenceConfiguration
    restaurants: list[RestaurantReviewConfidence]


class RecommendationThemeSignal(StrictModel):
    theme: str
    label: str
    mention_count: int = Field(gt=0)


class RestaurantRecommendationInsight(StrictModel):
    restaurant_id: str
    observation_count: int = Field(ge=0)
    latest_review_date: str
    positive_theme_mentions: int = Field(ge=0)
    negative_theme_mentions: int = Field(ge=0)
    positive_theme_counts: dict[str, int]
    negative_theme_counts: dict[str, int]
    top_positive_themes: list[RecommendationThemeSignal]
    top_negative_themes: list[RecommendationThemeSignal]


class RecommendationInsightMetadata(StrictModel):
    dataset_name: str
    builder_version: str
    restaurant_count: int = Field(ge=0)
    review_count: int = Field(ge=0)
    excluded_exact_duplicate_reviews: int = Field(ge=0)
    theme_limit_per_sentiment: int = Field(gt=0)
    synthetic_input: Literal[True]


class RecommendationInsightsDataset(StrictModel):
    metadata: RecommendationInsightMetadata
    restaurants: list[RestaurantRecommendationInsight]


RecommendationCategory = Literal[
    "best_overall",
    "best_walkable",
    "best_public_transportation",
    "best_value",
    "most_consistently_recommended",
    "best_vegetarian_match",
    "hidden_gem",
    "mixed_reviews",
]


class RecommendationBadge(StrictModel):
    category: RecommendationCategory
    label: str
    reason: str


class RecommendationTravel(StrictModel):
    starting_area: str
    walking_minutes: int = Field(gt=0)
    public_transit_minutes: int = Field(gt=0)
    driving_minutes: int = Field(gt=0)
    category: TravelConvenienceCategory
    selected_mode: TravelMode
    selected_minutes: int = Field(gt=0)
    explanation: str


class RestaurantRecommendationCard(StrictModel):
    rank: int = Field(gt=0)
    restaurant_id: str
    name: str
    address: str
    cuisine: str
    neighborhood: str
    price_category: Literal["$", "$$", "$$$"]
    estimated_cost_per_person: int = Field(gt=0)
    vegetarian_available: bool
    vegan_available: bool
    rating: float = Field(ge=1, le=5)
    dataset_review_count: int = Field(ge=0)
    total_score: float = Field(ge=0, le=100)
    categories: list[RecommendationBadge]
    travel: RecommendationTravel | None
    top_positive_themes: list[RecommendationThemeSignal]
    top_negative_themes: list[RecommendationThemeSignal]
    review_confidence_score: float = Field(ge=0, le=100)
    review_confidence_band: Literal["low", "medium", "high"]
    ranking_factors: dict[RankingFactor, RankingFactorScore]
    ranking_explanation: str
    latest_review_date: str
    data_freshness_label: str
    latest_inspection: LatestInspection


class RestaurantRecommendationResponse(StrictModel):
    filters: RestaurantSearchFilters
    configured_weights: RankingWeights
    match_count: int = Field(ge=0)
    assigned_categories: list[RecommendationCategory]
    recommendations: list[RestaurantRecommendationCard]
    data_notice: str


ConversationIntent = Literal[
    "walkable_only",
    "cheapest",
    "vegetarian_quality",
    "authenticity_priority",
    "review_reliability",
    "inspect_complaints",
    "show_all",
    "reset",
]
ConversationSortMode = Literal[
    "weighted",
    "cheapest",
    "preferred_theme",
    "review_confidence",
]
ConversationTravelPreference = Literal["any", "walkable"]
ConversationThemePreference = Literal[
    "vegetarian_options",
    "authenticity",
]


class RestaurantConversationState(StrictModel):
    filters: RestaurantSearchFilters = Field(default_factory=RestaurantSearchFilters)
    sort_mode: ConversationSortMode = "weighted"
    travel_preference: ConversationTravelPreference = "any"
    theme_preference: ConversationThemePreference | None = None
    result_limit: int | None = Field(default=None, gt=0, le=24)


class RestaurantConversationRequest(StrictModel):
    message: str = Field(min_length=1, max_length=300)
    state: RestaurantConversationState = Field(
        default_factory=RestaurantConversationState
    )

    @field_validator("message", mode="before")
    @classmethod
    def strip_message(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class RestaurantConversationResponse(StrictModel):
    intent: ConversationIntent
    state: RestaurantConversationState
    transition_explanation: str
    candidate_count_before_limit: int = Field(ge=0)
    results: RestaurantRecommendationResponse
