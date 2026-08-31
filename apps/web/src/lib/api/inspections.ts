export type InspectionResultFilter =
  | "all"
  | "pass"
  | "conditions"
  | "fail"
  | "other";

export type InspectionExplorerRequest = {
  latitude?: number;
  longitude?: number;
  radius_km: number;
  query?: string;
  result_filter: InspectionResultFilter;
  limit?: number;
};

export type PublicInspectionRestaurant = {
  license_number: string;
  name: string;
  alternate_name: string | null;
  facility_type: string;
  city_risk_category: string;
  address: string;
  latitude: number;
  longitude: number;
  distance_km: number | null;
  attention_level:
    | "latest_passed"
    | "conditions_noted"
    | "review_latest_report"
    | "informational";
  attention_label: string;
  latest_inspection: {
    inspection_id: string;
    inspection_date: string;
    result: string;
    inspection_type: string;
  };
  history: {
    records_in_query: number;
    pass_count: number;
    conditions_count: number;
    fail_count: number;
    other_count: number;
  };
};

export type InspectionExplorerResponse = {
  source_name: string;
  source_url: string;
  retrieved_at: string;
  source_record_count: number;
  restaurant_count: number;
  restaurants: PublicInspectionRestaurant[];
  data_notice: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonNegativeNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0;
}

function isInspectionRestaurant(
  value: unknown,
): value is PublicInspectionRestaurant {
  if (!isRecord(value)) return false;
  const latest = value.latest_inspection;
  const history = value.history;
  return (
    typeof value.license_number === "string" &&
    typeof value.name === "string" &&
    (value.alternate_name === null ||
      typeof value.alternate_name === "string") &&
    typeof value.facility_type === "string" &&
    typeof value.city_risk_category === "string" &&
    typeof value.address === "string" &&
    typeof value.latitude === "number" &&
    typeof value.longitude === "number" &&
    (value.distance_km === null || isNonNegativeNumber(value.distance_km)) &&
    [
      "latest_passed",
      "conditions_noted",
      "review_latest_report",
      "informational",
    ].includes(String(value.attention_level)) &&
    typeof value.attention_label === "string" &&
    isRecord(latest) &&
    typeof latest.inspection_id === "string" &&
    typeof latest.inspection_date === "string" &&
    typeof latest.result === "string" &&
    typeof latest.inspection_type === "string" &&
    isRecord(history) &&
    isNonNegativeNumber(history.records_in_query) &&
    isNonNegativeNumber(history.pass_count) &&
    isNonNegativeNumber(history.conditions_count) &&
    isNonNegativeNumber(history.fail_count) &&
    isNonNegativeNumber(history.other_count)
  );
}

export function parseInspectionExplorerResponse(
  value: unknown,
): InspectionExplorerResponse | null {
  if (!isRecord(value) || !Array.isArray(value.restaurants)) return null;
  if (
    typeof value.source_name !== "string" ||
    typeof value.source_url !== "string" ||
    typeof value.retrieved_at !== "string" ||
    !isNonNegativeNumber(value.source_record_count) ||
    !isNonNegativeNumber(value.restaurant_count) ||
    typeof value.data_notice !== "string" ||
    value.restaurant_count !== value.restaurants.length ||
    !value.restaurants.every(isInspectionRestaurant)
  ) {
    return null;
  }
  return value as InspectionExplorerResponse;
}

function apiErrorMessage(payload: unknown): string | null {
  if (!isRecord(payload)) return null;
  if (typeof payload.detail === "string") return payload.detail;
  return null;
}

export async function exploreInspections(
  request: InspectionExplorerRequest,
): Promise<InspectionExplorerResponse> {
  const response = await fetch("/api/restaurants/inspections", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(
      apiErrorMessage(payload) ??
        "Live inspection data could not be loaded. Please try again.",
    );
  }
  const parsed = parseInspectionExplorerResponse(payload);
  if (parsed === null) {
    throw new Error("The live inspection service returned an unexpected response.");
  }
  return parsed;
}
