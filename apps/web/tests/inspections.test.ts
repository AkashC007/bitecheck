import assert from "node:assert/strict";
import test from "node:test";

import { parseInspectionExplorerResponse } from "../src/lib/api/inspections.js";


const validResponse = {
  source_name: "City of Chicago Food Inspections",
  source_url: "https://data.cityofchicago.org/example",
  retrieved_at: "2026-08-31T12:00:00+00:00",
  source_record_count: 2,
  restaurant_count: 1,
  data_notice: "Historical observations only.",
  restaurants: [
    {
      license_number: "123",
      name: "REAL CAFE",
      alternate_name: null,
      facility_type: "Restaurant",
      city_risk_category: "Risk 1 (High)",
      address: "100 TEST ST, CHICAGO, IL, 60601",
      latitude: 41.8781,
      longitude: -87.6298,
      distance_km: 0.2,
      attention_level: "latest_passed",
      attention_label: "Latest inspection passed",
      latest_inspection: {
        inspection_id: "900",
        inspection_date: "2026-08-29",
        result: "Pass",
        inspection_type: "Canvass",
      },
      history: {
        records_in_query: 2,
        pass_count: 1,
        conditions_count: 0,
        fail_count: 1,
        other_count: 0,
      },
    },
  ],
};

test("parseInspectionExplorerResponse accepts source-backed cards", () => {
  assert.deepEqual(parseInspectionExplorerResponse(validResponse), validResponse);
});

test("parseInspectionExplorerResponse rejects mismatched counts", () => {
  assert.equal(
    parseInspectionExplorerResponse({ ...validResponse, restaurant_count: 2 }),
    null,
  );
});

test("parseInspectionExplorerResponse rejects malformed inspection history", () => {
  const malformed = structuredClone(validResponse);
  malformed.restaurants[0].history.fail_count = -1;

  assert.equal(parseInspectionExplorerResponse(malformed), null);
});
