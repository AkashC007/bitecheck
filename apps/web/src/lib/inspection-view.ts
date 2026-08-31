import type { PublicInspectionRestaurant } from "./api/inspections.js";


export type InspectionSortMode = "nearest" | "newest" | "name";

export type InspectionResultSummary = {
  total: number;
  passed: number;
  conditions: number;
  failed: number;
  other: number;
};

export function summarizeInspectionResults(
  restaurants: PublicInspectionRestaurant[],
): InspectionResultSummary {
  const summary: InspectionResultSummary = {
    total: restaurants.length,
    passed: 0,
    conditions: 0,
    failed: 0,
    other: 0,
  };
  for (const restaurant of restaurants) {
    if (restaurant.attention_level === "latest_passed") summary.passed += 1;
    else if (restaurant.attention_level === "conditions_noted") {
      summary.conditions += 1;
    } else if (restaurant.attention_level === "review_latest_report") {
      summary.failed += 1;
    } else summary.other += 1;
  }
  return summary;
}

function newestFirst(
  left: PublicInspectionRestaurant,
  right: PublicInspectionRestaurant,
) {
  return right.latest_inspection.inspection_date.localeCompare(
    left.latest_inspection.inspection_date,
  );
}

export function sortInspectionRestaurants(
  restaurants: PublicInspectionRestaurant[],
  mode: InspectionSortMode,
): PublicInspectionRestaurant[] {
  return [...restaurants].sort((left, right) => {
    if (mode === "name") return left.name.localeCompare(right.name);
    if (mode === "newest") {
      return newestFirst(left, right) || left.name.localeCompare(right.name);
    }
    if (left.distance_km === null && right.distance_km === null) {
      return newestFirst(left, right) || left.name.localeCompare(right.name);
    }
    if (left.distance_km === null) return 1;
    if (right.distance_km === null) return -1;
    return (
      left.distance_km - right.distance_km || left.name.localeCompare(right.name)
    );
  });
}
