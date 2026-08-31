import type {
  AppliedRestaurantSearchFilters,
  RestaurantSearchFilters,
} from "./restaurants.js";

export const RECOMMENDATION_CATEGORIES = [
  "best_overall",
  "best_walkable",
  "best_public_transportation",
  "best_value",
  "most_consistently_recommended",
  "best_vegetarian_match",
  "hidden_gem",
  "mixed_reviews",
] as const;

export type RecommendationCategory =
  (typeof RECOMMENDATION_CATEGORIES)[number];

export type RecommendationBadge = {
  category: RecommendationCategory;
  label: string;
  reason: string;
};

export type RecommendationTheme = {
  theme: string;
  label: string;
  mention_count: number;
};

export type RecommendationTravel = {
  starting_area: string;
  walking_minutes: number;
  public_transit_minutes: number;
  driving_minutes: number;
  category:
    | "walkable"
    | "comfortable_walk"
    | "easy_public_transit"
    | "longer_public_transit"
    | "easy_drive"
    | "inconvenient";
  selected_mode: "walking" | "public_transit" | "driving";
  selected_minutes: number;
  explanation: string;
};

export type LatestInspection = {
  inspection_id: string;
  inspection_date: string;
  result: "Pass" | "Pass w/ Conditions";
  inspection_type: string;
  risk: string;
};

export type RankingFactor = {
  status: "active" | "not_applicable" | "unavailable";
  score: number | null;
  configured_weight: number;
  effective_weight: number;
  contribution: number;
  explanation: string;
};

export type RestaurantRecommendation = {
  rank: number;
  restaurant_id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  cuisine: string;
  neighborhood: string;
  price_category: "$" | "$$" | "$$$";
  estimated_cost_per_person: number;
  vegetarian_available: boolean;
  vegan_available: boolean;
  rating: number;
  dataset_review_count: number;
  total_score: number;
  categories: RecommendationBadge[];
  travel: RecommendationTravel | null;
  top_positive_themes: RecommendationTheme[];
  top_negative_themes: RecommendationTheme[];
  review_confidence_score: number;
  review_confidence_band: "low" | "medium" | "high";
  ranking_factors: Record<string, RankingFactor>;
  ranking_explanation: string;
  latest_review_date: string;
  data_freshness_label: string;
  latest_inspection: LatestInspection;
};

export type RestaurantRecommendationResponse = {
  filters: AppliedRestaurantSearchFilters;
  configured_weights: Record<string, number>;
  match_count: number;
  assigned_categories: RecommendationCategory[];
  recommendations: RestaurantRecommendation[];
  data_notice: string;
};

const REQUEST_TIMEOUT_MS = 8_000;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isNullableNumber(value: unknown): value is number | null {
  return value === null || typeof value === "number";
}

function isFilters(value: unknown): value is AppliedRestaurantSearchFilters {
  return (
    isRecord(value) &&
    isNullableString(value.cuisine) &&
    isNullableNumber(value.maximum_budget) &&
    typeof value.vegetarian_required === "boolean" &&
    isNullableString(value.starting_area) &&
    isNullableNumber(value.maximum_travel_time)
  );
}

function isBadge(value: unknown): value is RecommendationBadge {
  return (
    isRecord(value) &&
    RECOMMENDATION_CATEGORIES.includes(
      value.category as RecommendationCategory,
    ) &&
    typeof value.label === "string" &&
    typeof value.reason === "string"
  );
}

function isTheme(value: unknown): value is RecommendationTheme {
  return (
    isRecord(value) &&
    typeof value.theme === "string" &&
    typeof value.label === "string" &&
    typeof value.mention_count === "number"
  );
}

function isTravel(value: unknown): value is RecommendationTravel {
  return (
    isRecord(value) &&
    typeof value.starting_area === "string" &&
    typeof value.walking_minutes === "number" &&
    typeof value.public_transit_minutes === "number" &&
    typeof value.driving_minutes === "number" &&
    typeof value.category === "string" &&
    (value.selected_mode === "walking" ||
      value.selected_mode === "public_transit" ||
      value.selected_mode === "driving") &&
    typeof value.selected_minutes === "number" &&
    typeof value.explanation === "string"
  );
}

function isLatestInspection(value: unknown): value is LatestInspection {
  return (
    isRecord(value) &&
    typeof value.inspection_id === "string" &&
    typeof value.inspection_date === "string" &&
    (value.result === "Pass" || value.result === "Pass w/ Conditions") &&
    typeof value.inspection_type === "string" &&
    typeof value.risk === "string"
  );
}

function isFactor(value: unknown): value is RankingFactor {
  return (
    isRecord(value) &&
    (value.status === "active" ||
      value.status === "not_applicable" ||
      value.status === "unavailable") &&
    isNullableNumber(value.score) &&
    typeof value.configured_weight === "number" &&
    typeof value.effective_weight === "number" &&
    typeof value.contribution === "number" &&
    typeof value.explanation === "string"
  );
}

function isRecommendation(value: unknown): value is RestaurantRecommendation {
  if (!isRecord(value) || !isRecord(value.ranking_factors)) {
    return false;
  }
  return (
    typeof value.rank === "number" &&
    typeof value.restaurant_id === "string" &&
    typeof value.name === "string" &&
    typeof value.address === "string" &&
    typeof value.latitude === "number" &&
    typeof value.longitude === "number" &&
    typeof value.cuisine === "string" &&
    typeof value.neighborhood === "string" &&
    (value.price_category === "$" ||
      value.price_category === "$$" ||
      value.price_category === "$$$") &&
    typeof value.estimated_cost_per_person === "number" &&
    typeof value.vegetarian_available === "boolean" &&
    typeof value.vegan_available === "boolean" &&
    typeof value.rating === "number" &&
    typeof value.dataset_review_count === "number" &&
    typeof value.total_score === "number" &&
    Array.isArray(value.categories) &&
    value.categories.every(isBadge) &&
    (value.travel === null || isTravel(value.travel)) &&
    Array.isArray(value.top_positive_themes) &&
    value.top_positive_themes.every(isTheme) &&
    Array.isArray(value.top_negative_themes) &&
    value.top_negative_themes.every(isTheme) &&
    typeof value.review_confidence_score === "number" &&
    (value.review_confidence_band === "low" ||
      value.review_confidence_band === "medium" ||
      value.review_confidence_band === "high") &&
    Object.values(value.ranking_factors).every(isFactor) &&
    typeof value.ranking_explanation === "string" &&
    typeof value.latest_review_date === "string" &&
    typeof value.data_freshness_label === "string" &&
    isLatestInspection(value.latest_inspection)
  );
}

export function parseRestaurantRecommendationResponse(
  value: unknown,
): RestaurantRecommendationResponse | null {
  if (
    !isRecord(value) ||
    !isFilters(value.filters) ||
    !isRecord(value.configured_weights) ||
    !Object.values(value.configured_weights).every(
      (weight) => typeof weight === "number",
    ) ||
    typeof value.match_count !== "number" ||
    !Array.isArray(value.assigned_categories) ||
    !value.assigned_categories.every((category) =>
      RECOMMENDATION_CATEGORIES.includes(category as RecommendationCategory),
    ) ||
    !Array.isArray(value.recommendations) ||
    !value.recommendations.every(isRecommendation) ||
    value.match_count !== value.recommendations.length ||
    typeof value.data_notice !== "string"
  ) {
    return null;
  }
  return value as RestaurantRecommendationResponse;
}

export function buildRecommendationRequest(
  filters: RestaurantSearchFilters,
): { filters: Record<string, string | number | boolean> } {
  const requestFilters: Record<string, string | number | boolean> = {
    vegetarian_required: filters.vegetarianRequired,
  };
  if (filters.cuisine) requestFilters.cuisine = filters.cuisine;
  if (filters.maximumBudget !== undefined) {
    requestFilters.maximum_budget = filters.maximumBudget;
  }
  if (filters.startingArea) requestFilters.starting_area = filters.startingArea;
  if (filters.maximumTravelTime !== undefined) {
    requestFilters.maximum_travel_time = filters.maximumTravelTime;
  }
  return { filters: requestFilters };
}

function readErrorMessage(value: unknown): string | null {
  if (!isRecord(value)) return null;
  if (typeof value.detail === "string") return value.detail;
  if (isRecord(value.detail) && typeof value.detail.message === "string") {
    return value.detail.message;
  }
  if (Array.isArray(value.detail) && isRecord(value.detail[0])) {
    const message = value.detail[0].msg;
    return typeof message === "string" ? message.replace(/^Value error, /, "") : null;
  }
  return null;
}

export async function recommendRestaurants(
  filters: RestaurantSearchFilters,
): Promise<RestaurantRecommendationResponse> {
  let response: Response;
  try {
    response = await fetch("/api/restaurants/recommendations", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(buildRecommendationRequest(filters)),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch {
    throw new Error(
      "BiteCheck could not reach the recommendation service. Please try again.",
    );
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error("BiteCheck received an unreadable response.");
  }
  if (!response.ok) {
    throw new Error(
      readErrorMessage(payload) ??
        `The recommendation request failed with status ${response.status}.`,
    );
  }
  const parsed = parseRestaurantRecommendationResponse(payload);
  if (parsed === null) {
    throw new Error("BiteCheck received an unexpected recommendation response.");
  }
  return parsed;
}
