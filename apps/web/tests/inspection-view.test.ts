import assert from "node:assert/strict";
import test from "node:test";

import type { PublicInspectionRestaurant } from "../src/lib/api/inspections.js";
import {
  sortInspectionRestaurants,
  summarizeInspectionResults,
} from "../src/lib/inspection-view.js";


function restaurant(
  name: string,
  date: string,
  distance: number | null,
  attentionLevel: PublicInspectionRestaurant["attention_level"],
): PublicInspectionRestaurant {
  return {
    license_number: name,
    name,
    alternate_name: null,
    facility_type: "Restaurant",
    city_risk_category: "Risk 1 (High)",
    address: "Chicago",
    latitude: 41.88,
    longitude: -87.63,
    distance_km: distance,
    attention_level: attentionLevel,
    attention_label: "Official result",
    latest_inspection: {
      inspection_id: name,
      inspection_date: date,
      result: "Pass",
      inspection_type: "Canvass",
    },
    history: {
      records_in_query: 1,
      pass_count: 1,
      conditions_count: 0,
      fail_count: 0,
      other_count: 0,
    },
  };
}

const restaurants = [
  restaurant("Bravo", "2026-08-20", 2.4, "conditions_noted"),
  restaurant("Alpha", "2026-08-25", 0.5, "latest_passed"),
  restaurant("Charlie", "2026-08-10", null, "review_latest_report"),
];

test("summarizeInspectionResults groups displayed latest results", () => {
  assert.deepEqual(summarizeInspectionResults(restaurants), {
    total: 3,
    passed: 1,
    conditions: 1,
    failed: 1,
    other: 0,
  });
});

test("sortInspectionRestaurants supports nearest and puts missing distance last", () => {
  assert.deepEqual(
    sortInspectionRestaurants(restaurants, "nearest").map((item) => item.name),
    ["Alpha", "Bravo", "Charlie"],
  );
});

test("sortInspectionRestaurants supports newest and name ordering", () => {
  assert.deepEqual(
    sortInspectionRestaurants(restaurants, "newest").map((item) => item.name),
    ["Alpha", "Bravo", "Charlie"],
  );
  assert.deepEqual(
    sortInspectionRestaurants(restaurants, "name").map((item) => item.name),
    ["Alpha", "Bravo", "Charlie"],
  );
});
