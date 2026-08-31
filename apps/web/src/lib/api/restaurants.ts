export const CUISINE_OPTIONS = [
  "American",
  "Chinese",
  "Ethiopian",
  "Indian",
  "Italian",
  "Japanese",
  "Korean",
  "Mediterranean",
  "Mexican",
  "Thai",
] as const;

export const STARTING_AREA_OPTIONS = [
  "Illinois Tech",
  "Chinatown",
  "Chicago Loop",
  "Hyde Park",
  "Bridgeport",
  "Lakeview",
  "River North",
] as const;

export type RestaurantSearchFilters = {
  cuisine?: string;
  maximumBudget?: number;
  vegetarianRequired: boolean;
  startingArea?: string;
  maximumTravelTime?: number;
};

export type AppliedRestaurantSearchFilters = {
  cuisine: string | null;
  maximum_budget: number | null;
  vegetarian_required: boolean;
  starting_area: string | null;
  maximum_travel_time: number | null;
};

export type TravelMatch = {
  starting_area: string;
  mode: "walking" | "public_transit";
  minutes: number;
};

export type RestaurantSearchItem = {
  restaurant_id: string;
  name: string;
  address: string;
  neighborhood: string;
  latitude: number;
  longitude: number;
  cuisine: string;
  price_category: "$" | "$$" | "$$$";
  estimated_cost_per_person: number;
  vegetarian_available: boolean;
  vegan_available: boolean;
  rating: number;
  review_count: number;
  travel: TravelMatch | null;
};

export type RestaurantSearchResponse = {
  applied_filters: AppliedRestaurantSearchFilters;
  match_count: number;
  restaurants: RestaurantSearchItem[];
};

const SEARCH_TIMEOUT_MS = 8_000;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isNullableNumber(value: unknown): value is number | null {
  return value === null || typeof value === "number";
}

function isTravelMatch(value: unknown): value is TravelMatch {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.starting_area === "string" &&
    (value.mode === "walking" || value.mode === "public_transit") &&
    typeof value.minutes === "number"
  );
}

function isRestaurantSearchItem(value: unknown): value is RestaurantSearchItem {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.restaurant_id === "string" &&
    typeof value.name === "string" &&
    typeof value.address === "string" &&
    typeof value.neighborhood === "string" &&
    typeof value.latitude === "number" &&
    typeof value.longitude === "number" &&
    typeof value.cuisine === "string" &&
    (value.price_category === "$" ||
      value.price_category === "$$" ||
      value.price_category === "$$$") &&
    typeof value.estimated_cost_per_person === "number" &&
    typeof value.vegetarian_available === "boolean" &&
    typeof value.vegan_available === "boolean" &&
    typeof value.rating === "number" &&
    typeof value.review_count === "number" &&
    (value.travel === null || isTravelMatch(value.travel))
  );
}

function isAppliedFilters(
  value: unknown,
): value is AppliedRestaurantSearchFilters {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNullableString(value.cuisine) &&
    isNullableNumber(value.maximum_budget) &&
    typeof value.vegetarian_required === "boolean" &&
    isNullableString(value.starting_area) &&
    isNullableNumber(value.maximum_travel_time)
  );
}

export function parseRestaurantSearchResponse(
  value: unknown,
): RestaurantSearchResponse | null {
  if (
    !isRecord(value) ||
    !isAppliedFilters(value.applied_filters) ||
    typeof value.match_count !== "number" ||
    !Array.isArray(value.restaurants) ||
    !value.restaurants.every(isRestaurantSearchItem) ||
    value.match_count !== value.restaurants.length
  ) {
    return null;
  }

  return value as RestaurantSearchResponse;
}

export function buildRestaurantSearchParams(
  filters: RestaurantSearchFilters,
): URLSearchParams {
  const params = new URLSearchParams();

  if (filters.cuisine) {
    params.set("cuisine", filters.cuisine);
  }
  if (filters.maximumBudget !== undefined) {
    params.set("maximum_budget", String(filters.maximumBudget));
  }
  if (filters.vegetarianRequired) {
    params.set("vegetarian_required", "true");
  }
  if (filters.startingArea) {
    params.set("starting_area", filters.startingArea);
  }
  if (filters.maximumTravelTime !== undefined) {
    params.set("maximum_travel_time", String(filters.maximumTravelTime));
  }

  return params;
}

function readErrorMessage(value: unknown): string | null {
  if (!isRecord(value)) {
    return null;
  }

  if (typeof value.detail === "string") {
    return value.detail;
  }

  if (isRecord(value.detail) && typeof value.detail.message === "string") {
    return value.detail.message;
  }

  if (Array.isArray(value.detail)) {
    const firstDetail = value.detail[0];
    if (isRecord(firstDetail) && typeof firstDetail.msg === "string") {
      return firstDetail.msg.replace(/^Value error, /, "");
    }
  }

  return null;
}

export async function searchRestaurants(
  filters: RestaurantSearchFilters,
): Promise<RestaurantSearchResponse> {
  const params = buildRestaurantSearchParams(filters);
  const query = params.size > 0 ? `?${params.toString()}` : "";

  let response: Response;
  try {
    response = await fetch(`/api/restaurants/search${query}`, {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(SEARCH_TIMEOUT_MS),
    });
  } catch {
    throw new Error(
      "BiteCheck could not reach the restaurant service. Please try again.",
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
        `The restaurant search failed with status ${response.status}.`,
    );
  }

  const parsed = parseRestaurantSearchResponse(payload);
  if (parsed === null) {
    throw new Error("BiteCheck received an unexpected restaurant response.");
  }

  return parsed;
}
